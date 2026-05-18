from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.models.stock import Stock
from app.models.trade_history import TradeHistory
from app.models.executed_trade import ExecutedTrade
from app.models.order import Order
from app.models.candle import Candle
from app.schemas.trade import StockResponse, TradeHistoryResponse
from app.schemas.order import BookLevel, BookSnapshot
from app.services.candle_service import CandleService

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_model=list[StockResponse])
def get_stocks(db: Session = Depends(get_db)):
    """Get all stocks. Pricing is now determined by actual trades, not random fluctuations."""
    stocks = db.query(Stock).all()
    return stocks


@router.get("/{stock_id}", response_model=StockResponse)
def get_stock(stock_id: int, db: Session = Depends(get_db)):
    """Get a single stock by ID."""
    stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")
    return stock


@router.get("/{stock_id}/book", response_model=BookSnapshot)
def get_order_book(stock_id: int, limit: int = 5, db: Session = Depends(get_db)):
    """
    Get the order book (top levels) for a stock.
    
    Returns the top `limit` bid levels and ask levels.
    Bid side is sorted highest-first (best bid on top).
    Ask side is sorted lowest-first (best ask on top).
    """
    stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")
    
    # Fetch top bids (highest price first)
    bids_rows = (
        db.query(Order.price, Order.remaining_qty)
        .filter(
            Order.stock_id == stock_id,
            Order.side == "BUY",
            Order.status.in_(("OPEN", "PARTIAL")),
            Order.remaining_qty > 0,
        )
        .order_by(Order.price.desc(), Order.created_at.asc())
        .limit(limit)
        .all()
    )
    
    # Fetch top asks (lowest price first)
    asks_rows = (
        db.query(Order.price, Order.remaining_qty)
        .filter(
            Order.stock_id == stock_id,
            Order.side == "SELL",
            Order.status.in_(("OPEN", "PARTIAL")),
            Order.remaining_qty > 0,
        )
        .order_by(Order.price.asc(), Order.created_at.asc())
        .limit(limit)
        .all()
    )
    
    return {
        "stock_id": stock_id,
        "bids": [BookLevel(price=float(p), quantity=int(q)) for p, q in bids_rows],
        "asks": [BookLevel(price=float(p), quantity=int(q)) for p, q in asks_rows],
    }


class CandleResponse:
    """Response model for a single candle."""
    id: int
    stock_id: int
    resolution: str
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@router.get("/{stock_id}/candles", response_model=List[dict])
def get_candles(
    stock_id: int,
    resolution: str = "5m",
    limit: int = 200,
    db: Session = Depends(get_db),
):
    """
    Get OHLCV candles for a stock.
    
    Args:
        stock_id: The stock ID
        resolution: '1m', '5m', or '1h'
        limit: Number of candles to return (default 200)
    
    Returns: List of candles in ascending order by open_time (oldest first).
    """
    valid_resolutions = ("1m", "5m", "1h", "1D", "1W")
    if resolution not in valid_resolutions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid resolution. Must be 1m, 5m, 1h, 1D, or 1W.")
    
    stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")

    if resolution in ("1m", "5m", "1h"):
        # Only use actual traded candle records for intraday resolutions.
        # Real market intraday bars should derive from executed candles,
        # not from a raw history fallback when no traded candle exists.
        existing_candles = (
            db.query(Candle)
            .filter(Candle.stock_id == stock_id, Candle.resolution == resolution)
            .order_by(Candle.open_time.asc())
            .all()
        )
        actual_candles = [c for c in existing_candles if c.volume > 0]

        from app.services.candle_service import CandleService
        now = datetime.now(timezone.utc)
        periods_to_generate = 24 * 3600 // CandleService.RESOLUTIONS[resolution]
        current_time = CandleService._floor_to_resolution(now, resolution)

        if not actual_candles:
            history = (
                db.query(ExecutedTrade)
                .filter(ExecutedTrade.stock_id == stock_id)
                .order_by(ExecutedTrade.timestamp.asc())
                .all()
            )
            if not history:
                return []

            candle_map = {}
            for trade in history:
                bucket = CandleService._floor_to_resolution(trade.timestamp, resolution)
                if bucket not in candle_map:
                    candle_map[bucket] = {
                        "id": 0,
                        "stock_id": stock_id,
                        "resolution": resolution,
                        "open_time": bucket,
                        "open": trade.price,
                        "high": trade.price,
                        "low": trade.price,
                        "close": trade.price,
                        "volume": trade.quantity,
                    }
                else:
                    entry = candle_map[bucket]
                    entry["high"] = max(entry["high"], trade.price)
                    entry["low"] = min(entry["low"], trade.price)
                    entry["close"] = trade.price
                    entry["volume"] += trade.quantity

            candles = sorted(candle_map.values(), key=lambda c: c["open_time"])[-limit:]
            return [
                {
                    "id": c["id"],
                    "stock_id": c["stock_id"],
                    "resolution": c["resolution"],
                    "open_time": c["open_time"].isoformat(),
                    "open": c["open"],
                    "high": c["high"],
                    "low": c["low"],
                    "close": c["close"],
                    "volume": c["volume"],
                }
                for c in candles
            ]

        candle_map = {c.open_time: c for c in actual_candles}
        generated_candles = []
        last_price = actual_candles[-1].close
        latest_actual_time = actual_candles[-1].open_time

        for _ in range(periods_to_generate):
            if current_time in candle_map:
                candle = candle_map[current_time]
                generated_candles.append(candle)
                last_price = candle.close
            elif current_time > latest_actual_time:
                generated_candles.append({
                    "id": 0,
                    "stock_id": stock_id,
                    "resolution": resolution,
                    "open_time": current_time,
                    "open": last_price,
                    "high": last_price,
                    "low": last_price,
                    "close": last_price,
                    "volume": 0,
                })
            current_time -= timedelta(seconds=CandleService.RESOLUTIONS[resolution])

        candles = sorted(generated_candles, key=lambda c: c["open_time"] if isinstance(c, dict) else c.open_time)[-limit:]

        return [
            {
                "id": c["id"] if isinstance(c, dict) else c.id,
                "stock_id": c["stock_id"] if isinstance(c, dict) else c.stock_id,
                "resolution": c["resolution"] if isinstance(c, dict) else c.resolution,
                "open_time": (c["open_time"].isoformat() if isinstance(c, dict) else c.open_time.isoformat()),
                "open": c["open"] if isinstance(c, dict) else c.open,
                "high": c["high"] if isinstance(c, dict) else c.high,
                "low": c["low"] if isinstance(c, dict) else c.low,
                "close": c["close"] if isinstance(c, dict) else c.close,
                "volume": c["volume"] if isinstance(c, dict) else c.volume,
            }
            for c in candles
        ]

    # Build aggregated daily / weekly candles from actual executed trades when those resolutions are requested.
    history = (
        db.query(ExecutedTrade)
        .filter(ExecutedTrade.stock_id == stock_id)
        .order_by(ExecutedTrade.timestamp.asc())
        .all()
    )

    if not history:
        return []

    def floor_to_resolution(ts: datetime, res: str) -> datetime:
        date = ts.date()
        if res == "1D":
            return datetime(date.year, date.month, date.day)
        if res == "1W":
            start_of_week = date - timedelta(days=date.weekday())
            return datetime(start_of_week.year, start_of_week.month, start_of_week.day)
        raise ValueError("Unsupported resolution")

    grouped = {}
    for trade in history:
        bucket = floor_to_resolution(trade.timestamp, resolution)
        if bucket not in grouped:
            grouped[bucket] = {
                "open_time": bucket,
                "open": trade.price,
                "high": trade.price,
                "low": trade.price,
                "close": trade.price,
                "volume": trade.quantity,
            }
        else:
            group = grouped[bucket]
            group["high"] = max(group["high"], trade.price)
            group["low"] = min(group["low"], trade.price)
            group["close"] = trade.price
            group["volume"] += trade.quantity

    candles = [grouped[key] for key in sorted(grouped.keys())][-limit:]
    return [
        {
            "id": i + 1,
            "stock_id": stock_id,
            "resolution": resolution,
            "open_time": candle["open_time"].isoformat(),
            "open": candle["open"],
            "high": candle["high"],
            "low": candle["low"],
            "close": candle["close"],
            "volume": candle["volume"],
        }
        for i, candle in enumerate(candles)
    ]


@router.get("/price-history/{stock_id}", response_model=list[TradeHistoryResponse])
def get_price_history(stock_id: int, limit: int = 200, db: Session = Depends(get_db)):
    """
    DEPRECATED: Use /candles endpoint instead.
    
    Get price history for a stock. Returns raw trade ticks (not aggregated into candles).
    For charting, prefer /candles which returns OHLCV data.
    """
    history = db.query(TradeHistory).filter(
        TradeHistory.stock_id == stock_id
    ).order_by(TradeHistory.timestamp.asc()).limit(limit).all()
    return history
