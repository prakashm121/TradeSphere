from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.stock import Stock
from app.models.trade_history import TradeHistory
from app.schemas.trade import StockResponse, TradeHistoryResponse

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_model=list[StockResponse])
def get_stocks(db: Session = Depends(get_db)):
    """Get all stocks. Pricing is now determined by actual trades, not random fluctuations."""
    stocks = db.query(Stock).all()
    return stocks


@router.get("/price-history/{stock_id}", response_model=list[TradeHistoryResponse])
def get_price_history(stock_id: int, limit: int = 200, db: Session = Depends(get_db)):
    """Get price history for a stock. Used for charting."""
    history = db.query(TradeHistory).filter(
        TradeHistory.stock_id == stock_id
    ).order_by(TradeHistory.timestamp.asc()).limit(limit).all()
    return history
