"""
CandleService: Aggregates executed trades into OHLCV candles.

For each trade tick, updates candles across all three resolutions (1m, 5m, 1h).
Candles are generated lazily on first trade in each window.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.candle import Candle
from app.models.stock import Stock

logger = logging.getLogger(__name__)


class CandleService:
    """Update OHLCV candles from executed trade data."""

    RESOLUTIONS = {
        "1m": 60,          # 1 minute in seconds
        "5m": 300,         # 5 minutes
        "1h": 3600,        # 1 hour
    }

    @staticmethod
    def _floor_to_resolution(ts: datetime, resolution: str) -> datetime:
        """
        Floor a timestamp to the start of its resolution window.
        
        Example: 14:37:45 with 5m → 14:35:00
        """
        if resolution not in CandleService.RESOLUTIONS:
            raise ValueError(f"Unknown resolution: {resolution}")
        
        seconds = CandleService.RESOLUTIONS[resolution]
        epoch = ts.replace(hour=0, minute=0, second=0, microsecond=0)
        delta = int((ts - epoch).total_seconds() // seconds) * seconds
        return epoch + timedelta(seconds=delta)

    @staticmethod
    def update(db: Session, stock_id: int, trade_price: float, trade_qty: int, trade_ts: datetime) -> None:
        """
        Update all candles (1m, 5m, 1h) for a stock after a trade executes.
        
        Args:
            db: SQLAlchemy session
            stock_id: Which stock the trade is on
            trade_price: Execution price
            trade_qty: Quantity traded
            trade_ts: When the trade happened
        """
        updated_candles = []
        for resolution in CandleService.RESOLUTIONS:
            candle = CandleService._update_candle_for_resolution(db, stock_id, resolution, trade_price, trade_qty, trade_ts)
            updated_candles.append(candle)
        return updated_candles

    @staticmethod
    def _update_candle_for_resolution(
        db: Session,
        stock_id: int,
        resolution: str,
        trade_price: float,
        trade_qty: int,
        trade_ts: datetime,
    ) -> None:
        """Update a single candle for a specific resolution."""
        open_time = CandleService._floor_to_resolution(trade_ts, resolution)
        
        # Fetch or create candle, locked for update
        candle = (
            db.query(Candle)
            .filter(
                Candle.stock_id == stock_id,
                Candle.resolution == resolution,
                Candle.open_time == open_time,
            )
            .with_for_update()
            .first()
        )

        if candle is None:
            # New candle — open = close = trade price
            candle = Candle(
                stock_id=stock_id,
                resolution=resolution,
                open_time=open_time,
                open=trade_price,
                high=trade_price,
                low=trade_price,
                close=trade_price,
                volume=trade_qty,
            )
            db.add(candle)
        else:
            # Update existing candle
            candle.high = max(candle.high, trade_price)
            candle.low = min(candle.low, trade_price)
            candle.close = trade_price
            candle.volume += trade_qty

        return candle
