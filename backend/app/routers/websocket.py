"""
WebSocket Router: Market event streaming endpoint.

Clients connect to /ws/market and receive real-time:
  - price updates (stock_id, price, bid, ask)
  - trade ticks (stock_id, qty, price, aggressor_side)
  - book snapshots (bids, asks)
"""
import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.order import Order
from app.models.stock import Stock
from app.services import ws_hub
from app.schemas.order import BookLevel, BookSnapshot

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/market")
async def market_ws(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for market data streaming.
    
    Connects on: ws://api/ws/market
    
    On connect, sends initial book snapshot for all stocks.
    Then streams events from broadcast hub:
      - price_update
      - trade_tick
      - book_snapshot
    """
    await websocket.accept()
    client_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    
    # Register client with hub
    ws_hub.register_client(client_queue)
    
    try:
        # Send initial full snapshot on connect
        initial_snapshot = _get_full_market_snapshot()
        await websocket.send_json({
            "type": "market_snapshot",
            "data": initial_snapshot,
            "timestamp": str(datetime.utcnow().isoformat()),
        })
        
        # Listen for events from hub
        while True:
            try:
                event = await asyncio.wait_for(client_queue.get(), timeout=30.0)
                await websocket.send_json(event)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "heartbeat"})
            except WebSocketDisconnect:
                break
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    
    finally:
        ws_hub.unregister_client(client_queue)
        try:
            await websocket.close()
        except Exception as close_error:
            logger.debug(f"WebSocket close ignored: {close_error}")


def _get_full_market_snapshot() -> dict:
    """
    Get a complete snapshot of all stocks and their order books.
    Sent to new clients on connect.
    """
    db = SessionLocal()
    try:
        stocks = db.query(Stock).all()
        snapshot = {}
        
        for stock in stocks:
            snapshot[stock.symbol] = {
                "stock_id": stock.stock_id,
                "symbol": stock.symbol,
                "name": stock.name,
                "last_price": stock.last_traded_price or stock.price,
                "bid": stock.bid_price,
                "ask": stock.ask_price,
                "book": _get_order_book(db, stock.stock_id),
            }
        
        return snapshot
    
    finally:
        db.close()


def _get_order_book(db: Session, stock_id: int, top_n: int = 5) -> dict:
    """Get top N levels of the order book for a stock."""
    bids = (
        db.query(Order.price, Order.remaining_qty)
        .filter(
            Order.stock_id == stock_id,
            Order.side == "BUY",
            Order.status.in_(("OPEN", "PARTIAL")),
            Order.remaining_qty > 0,
        )
        .order_by(Order.price.desc(), Order.created_at.asc())
        .limit(top_n)
        .all()
    )
    
    asks = (
        db.query(Order.price, Order.remaining_qty)
        .filter(
            Order.stock_id == stock_id,
            Order.side == "SELL",
            Order.status.in_(("OPEN", "PARTIAL")),
            Order.remaining_qty > 0,
        )
        .order_by(Order.price.asc(), Order.created_at.asc())
        .limit(top_n)
        .all()
    )
    
    return {
        "bids": [{"price": float(price), "quantity": int(qty)} for price, qty in bids],
        "asks": [{"price": float(price), "quantity": int(qty)} for price, qty in asks],
    }


async def emit_price_update(stock_id: int) -> None:
    """Broadcast a price update event."""
    db = SessionLocal()
    try:
        stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
        if not stock:
            return

        event = {
            "type": "price_update",
            "stock_id": stock_id,
            "price": float(stock.last_traded_price or stock.price),
            "bid": stock.bid_price,
            "ask": stock.ask_price,
            "timestamp": str(datetime.utcnow().isoformat()),
        }
        await ws_hub.broadcast(event)
    finally:
        db.close()


async def emit_trade_tick(stock_id: int, price: float, quantity: int, aggressor_side: str) -> None:
    """Broadcast a trade tick event."""
    event = {
        "type": "trade_tick",
        "stock_id": stock_id,
        "price": price,
        "quantity": quantity,
        "aggressor_side": aggressor_side,
        "timestamp": str(datetime.utcnow().isoformat()),
    }
    await ws_hub.broadcast(event)


async def emit_book_snapshot(stock_id: int) -> None:
    """Broadcast an order book snapshot."""
    db = SessionLocal()
    try:
        book = _get_order_book(db, stock_id, top_n=10)
        event = {
            "type": "book_snapshot",
            "stock_id": stock_id,
            "bids": book["bids"],
            "asks": book["asks"],
            "timestamp": str(datetime.utcnow().isoformat()),
        }
        await ws_hub.broadcast(event)
    finally:
        db.close()


async def emit_order_update(order: dict) -> None:
    """Broadcast an order status update event from a detached-safe payload."""
    event = {
        "type": "order_update",
        "order_id": order["order_id"],
        "stock_id": order["stock_id"],
        "status": order["status"],
        "filled_qty": order["filled_qty"],
        "remaining_qty": order["remaining_qty"],
        "order_type": order["order_type"],
        "side": order["side"],
        "price": order["price"],
        "timestamp": str(datetime.utcnow().isoformat()),
    }
    await ws_hub.broadcast(event)
