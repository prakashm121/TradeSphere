"""
Market Maker - Background worker that simulates market activity.
Without this, the market is dead. This creates realistic price movement
by executing random BUY/SELL trades at regular intervals.
"""
import asyncio
import random
import logging
from datetime import datetime
from app.core.database import SessionLocal
from app.models.stock import Stock
from app.models.trade_history import TradeHistory

logger = logging.getLogger(__name__)


def simulate_trade(db):
    """Simulate a single random trade that moves the price."""
    stocks = db.query(Stock).all()
    if not stocks:
        return

    stock = random.choice(stocks)

    # Lock the stock row
    stock = db.query(Stock).filter(
        Stock.stock_id == stock.stock_id
    ).with_for_update().first()

    if not stock:
        return

    trade_type = random.choice(["BUY", "SELL"])
    quantity = random.randint(1, 50)

    base_price = stock.price

    # Volume-based impact (same formula as TradeService)
    impact = (quantity * 0.00005)

    # Add a small random noise for more realistic movement
    noise = random.uniform(-0.001, 0.001)

    if trade_type == "BUY":
        base_price *= (1 + impact + noise)
    else:
        base_price *= (1 - impact + noise)

    # Clamp - price never below 0.01
    new_price = round(max(base_price, 0.01), 2)
    stock.price = new_price

    # Store in trade history for the graph
    db.add(TradeHistory(
        stock_id=stock.stock_id,
        price=new_price,
        quantity=quantity,
        timestamp=datetime.utcnow()
    ))

    db.commit()
    logger.debug(f"Market maker: {trade_type} {quantity} of {stock.symbol} -> ${new_price}")


async def market_maker():
    """Background task that continuously simulates market activity."""
    logger.info("Market maker started")
    while True:
        db = SessionLocal()
        try:
            simulate_trade(db)
        except Exception as e:
            db.rollback()
            logger.error(f"Market maker error: {e}")
        finally:
            db.close()
        
        # Run every 5 seconds
        await asyncio.sleep(5)
