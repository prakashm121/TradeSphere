from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import random
from app.core.database import get_db
from app.models.stock import Stock
from app.schemas.trade import StockResponse

router = APIRouter(prefix="/stocks", tags=["stocks"])

last_price_update = datetime.now()


def update_stock_prices(db: Session):
    """Update stock prices with random fluctuations."""
    global last_price_update
    current_time = datetime.now()
    time_since_last_update = (current_time - last_price_update).total_seconds()
    
    if time_since_last_update < 30:
        return
    
    stocks = db.query(Stock).all()
    for stock in stocks:
        change_percent = random.uniform(-0.35, 0.35)
        new_price = stock.price * (1 + change_percent)
        new_price = round(max(new_price, 1.0), 2)
        stock.price = new_price
    
    db.commit()
    last_price_update = current_time


@router.get("", response_model=list[StockResponse])
def get_stocks(db: Session = Depends(get_db)):
    """Get all stocks with updated prices."""
    update_stock_prices(db)
    stocks = db.query(Stock).all()
    return stocks

