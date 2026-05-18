"""
Candlestick Engine: Background task that aggregates trades into OHLCV candles.

Subscribes to trade_tick events from the WebSocket broadcast hub and updates
candles for all supported resolutions.
"""
import asyncio
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services import ws_hub
from app.services.candle_service import CandleService
from app.services.ws_hub import register_client, unregister_client

logger = logging.getLogger(__name__)

# Database session factory
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


async def candle_engine() -> None:
    """
    Background task: consume trade_tick events and update candles.
    """

    if ws_hub.broadcast_queue is None:
        logger.error("broadcast_queue not initialized; cannot start candle engine")
        return

    logger.info("Candle engine started")
    client_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
    register_client(client_queue)

    try:
        while True:
            try:
                event = await client_queue.get()
                if event.get("type") != "trade_tick":
                    continue

                timestamp = event.get("timestamp")
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)

                await process_trade_tick(
                    stock_id=int(event.get("stock_id")),
                    trade_price=float(event.get("price")),
                    trade_qty=int(event.get("quantity")),
                    trade_ts=timestamp,
                )
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Candle engine error: {e}")
                await asyncio.sleep(1)
    finally:
        unregister_client(client_queue)


def _save_trade_tick_candles(stock_id: int, trade_price: float, trade_qty: int, trade_ts: datetime) -> list[dict]:
    """Sync helper to update candles and return plain payloads."""
    db = SessionLocal()
    try:
        updated_candles = CandleService.update(db, stock_id, trade_price, trade_qty, trade_ts)
        db.commit()

        candle_payloads = []
        for candle in updated_candles:
            candle_payloads.append({
                "resolution": candle.resolution,
                "candle": {
                    "id": candle.id,
                    "stock_id": candle.stock_id,
                    "resolution": candle.resolution,
                    "open_time": candle.open_time.isoformat(),
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume,
                },
            })
        return candle_payloads
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing trade tick: {e}")
        return []
    finally:
        db.close()


async def process_trade_tick(stock_id: int, trade_price: float, trade_qty: int, trade_ts: datetime) -> None:
    """
    Called by the candle engine after a trade tick event.
    Updates all candles and broadcasts candle_update events.
    """
    candle_payloads = await asyncio.to_thread(
        _save_trade_tick_candles,
        stock_id,
        trade_price,
        trade_qty,
        trade_ts,
    )

    for payload in candle_payloads:
        await ws_hub.broadcast({
            "type": "candle_update",
            "stock_id": stock_id,
            "resolution": payload["resolution"],
            "candle": payload["candle"],
            "timestamp": trade_ts.isoformat(),
        })
