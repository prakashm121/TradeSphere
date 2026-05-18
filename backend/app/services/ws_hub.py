"""
WebSocket Hub: Central event broadcaster for all market events.

Design:
  - Global broadcast_queue: Matches push events from trade engine
  - Per-client queues: Each connected client has its own queue
  - Hub task: Reads from broadcast and fans out to all subscribers
  - Client task: Each client reads from its queue and sends over WS

This decouples the trade engine (fast path) from WebSocket I/O (potentially slow).
"""
import asyncio
import json
import logging
from typing import Callable
from datetime import datetime

logger = logging.getLogger(__name__)

# Global state
broadcast_queue: asyncio.Queue | None = None
client_queues: set[asyncio.Queue] = set()
hub_task: asyncio.Task | None = None


def event_to_json(event: dict) -> str:
    """Serialize an event dict to JSON, handling datetime objects."""
    def default_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    return json.dumps(event, default=default_serializer)


async def broadcast(event: dict) -> None:
    """
    Emit an event to all connected WebSocket clients.
    
    Called from trade engine after fills commit.
    Non-blocking: puts event on broadcast queue and returns immediately.
    """
    global broadcast_queue
    if broadcast_queue is None:
        logger.warning("broadcast_queue not initialized; dropping event")
        return
    
    try:
        broadcast_queue.put_nowait(event)
    except asyncio.QueueFull:
        logger.error("broadcast_queue full; dropping event")


async def hub_task_runner() -> None:
    """
    Background task: read from broadcast queue and fan out to all clients.
    
    Runs forever. Subscribe to this in app lifespan.
    """
    global broadcast_queue, client_queues
    
    logger.info("WebSocket hub started")
    
    while True:
        try:
            # Wait for next event from trade engine
            event = await broadcast_queue.get()
            
            # Fan out to all connected clients
            for q in list(client_queues):
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    # Client's queue full; likely dead or slow. Log and skip.
                    logger.warning(f"Client queue full; client may be disconnected")
        except Exception as e:
            logger.error(f"Hub task error: {e}")
            await asyncio.sleep(1)


async def init_hub(max_broadcast_queue_size: int = 1000) -> None:
    """Initialize the hub. Call this in app startup."""
    global broadcast_queue, hub_task
    
    if broadcast_queue is not None:
        logger.warning("Hub already initialized")
        return
    
    broadcast_queue = asyncio.Queue(maxsize=max_broadcast_queue_size)
    hub_task = asyncio.create_task(hub_task_runner())
    logger.info("Hub initialized")


async def shutdown_hub() -> None:
    """Clean up hub on shutdown."""
    global hub_task
    if hub_task:
        hub_task.cancel()
        try:
            await hub_task
        except asyncio.CancelledError:
            pass
    logger.info("Hub shutdown")


def register_client(q: asyncio.Queue) -> None:
    """Register a new client connection."""
    global client_queues
    client_queues.add(q)
    logger.debug(f"Client registered. Total clients: {len(client_queues)}")


def unregister_client(q: asyncio.Queue) -> None:
    """Unregister a client on disconnect."""
    global client_queues
    client_queues.discard(q)
    logger.debug(f"Client unregistered. Total clients: {len(client_queues)}")
