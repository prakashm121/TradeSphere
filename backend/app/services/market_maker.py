"""
Market Maker Bots - v2: Realistic order placement.

The bots are liquidity providers. They do NOT trade randomly. Instead, they:
1. Read the current mid-price (from bid/ask or last trade)
2. Cancel stale quotes (orders too far from the new mid)
3. Place new BUY limit order at mid × (1 - spread/2)
4. Place new SELL limit order at mid × (1 + spread/2)

Spread is dynamic based on recent volatility. This creates realistic market behavior
where spreads widen when markets move sharply.

The bot needs a dedicated user account to place orders. This account is seeded
with a large balance at app startup.
"""
import asyncio
import random
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.models.user import User
from app.models.stock import Stock
from app.models.order import Order
from app.models.executed_trade import ExecutedTrade
from app.services.trade_service import TradeService
from app.schemas.order import OrderRequest

logger = logging.getLogger(__name__)

# Database session
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

# Bot configuration
BOT_USER_EMAIL = "bot@tradesphere.internal"
BOT_INITIAL_BALANCE = 999_999_999.0
BOT_QUOTE_REFRESH_INTERVAL = 5  # seconds
BOT_STALE_DISTANCE = 0.02  # 2% — cancel orders if mid moved > 2%
BOT_ORDER_SIZE_MIN = 10
BOT_ORDER_SIZE_MAX = 80
BOT_BASE_SPREAD = 0.004  # 0.4% — base spread from mid


def _get_or_create_bot_user(db: Session) -> User:
    """Fetch the bot user, or create it if missing."""
    bot = db.query(User).filter(User.email == BOT_USER_EMAIL).first()
    if bot:
        return bot
    
    logger.info(f"Creating bot user: {BOT_USER_EMAIL}")
    bot = User(
        email=BOT_USER_EMAIL,
        password="",  # No password needed; bots never log in
        balance=BOT_INITIAL_BALANCE,
        margin_held=0.0,
        is_verified=True,
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot


def _compute_spread(db: Session, stock_id: int, base_spread: float = BOT_BASE_SPREAD) -> float:
    """
    Compute dynamic spread based on recent volatility.
    
    If market is calm (few recent trades), use base spread.
    If market is volatile, widen the spread proportionally.
    """
    # Get last 20 executed trades for volatility measurement
    trades = (
        db.query(ExecutedTrade.price)
        .filter(ExecutedTrade.stock_id == stock_id)
        .order_by(ExecutedTrade.timestamp.desc())
        .limit(20)
        .all()
    )
    
    if len(trades) < 5:
        return base_spread
    
    prices = [float(price) for price, in trades]
    prices.reverse()  # Oldest first
    
    # Compute returns (price changes)
    returns = []
    for i in range(1, len(prices)):
        if prices[i - 1] != 0:
            ret = abs(prices[i] / prices[i - 1] - 1)
            returns.append(ret)
    
    if not returns:
        return base_spread
    
    # Average absolute return = volatility
    volatility = sum(returns) / len(returns)
    
    # Widen spread proportionally to volatility, capped at 5%
    spread = max(base_spread, min(volatility * 10, 0.05))
    logger.debug(f"Stock {stock_id}: volatility={volatility:.4f} -> spread={spread:.4f}")
    return spread


def _get_mid_price(db: Session, stock: Stock) -> float | None:
    """
    Get current mid-price for the stock.
    Prefers (bid + ask) / 2, falls back to last_traded_price.
    """
    if stock.bid_price is not None and stock.ask_price is not None:
        return (stock.bid_price + stock.ask_price) / 2
    
    if stock.last_traded_price is not None:
        return stock.last_traded_price
    
    return None


def _cancel_stale_quotes(db: Session, bot_user_id: int, stock_id: int, mid_price: float) -> int:
    """
    Cancel the bot's resting orders that are too far from the new mid-price.
    
    Returns: Number of orders cancelled.
    """
    resting = (
        db.query(Order)
        .filter(
            Order.user_id == bot_user_id,
            Order.stock_id == stock_id,
            Order.status.in_(("OPEN", "PARTIAL")),
        )
        .with_for_update()
        .all()
    )
    
    cancelled = 0
    for order in resting:
        if order.price is None:
            continue
        
        # Check if order price is > stale_distance from mid
        distance = abs(order.price - mid_price) / mid_price
        if distance > BOT_STALE_DISTANCE:
            logger.debug(
                f"Bot: cancelling stale {order.side} order #{order.id} at {order.price} "
                f"(mid={mid_price}, distance={distance:.2%})"
            )
            order.status = "CANCELLED"
            cancelled += 1
    
    return cancelled


def _place_bot_quotes(db: Session, bot: User, stock: Stock) -> None:
    """
    Place new BUY and SELL limit orders around the mid-price.
    
    BUY at mid × (1 - spread/2)
    SELL at mid × (1 + spread/2)
    """
    mid_price = _get_mid_price(db, stock)
    if mid_price is None or mid_price <= 0:
        logger.warning(f"Cannot place quotes for stock {stock.stock_id}: no valid mid price")
        return
    
    spread = _compute_spread(db, stock.stock_id)
    
    # Randomize order sizes for realism
    buy_qty = random.randint(BOT_ORDER_SIZE_MIN, BOT_ORDER_SIZE_MAX)
    sell_qty = random.randint(BOT_ORDER_SIZE_MIN, BOT_ORDER_SIZE_MAX)
    
    # Place BUY at bid (mid - spread/2)
    buy_price = round(mid_price * (1 - spread / 2), 2)
    try:
        TradeService.place_order(
            db=db,
            user_id=bot.user_id,
            stock_id=stock.stock_id,
            side="BUY",
            order_type="LIMIT",
            quantity=buy_qty,
            price=buy_price,
        )
        logger.debug(f"Bot: placed BUY {buy_qty} @ {buy_price} for stock {stock.symbol}")
    except Exception as e:
        logger.error(f"Bot: failed to place BUY order: {e}")
        db.rollback()
    
    # Place SELL at ask (mid + spread/2)
    sell_price = round(mid_price * (1 + spread / 2), 2)
    try:
        TradeService.place_order(
            db=db,
            user_id=bot.user_id,
            stock_id=stock.stock_id,
            side="SELL",
            order_type="LIMIT",
            quantity=sell_qty,
            price=sell_price,
        )
        logger.debug(f"Bot: placed SELL {sell_qty} @ {sell_price} for stock {stock.symbol}")
    except Exception as e:
        logger.error(f"Bot: failed to place SELL order: {e}")
        db.rollback()


def _init_bot_user() -> int:
    db = SessionLocal()
    try:
        bot = _get_or_create_bot_user(db)
        return bot.user_id
    finally:
        db.close()


def _run_market_maker_cycle(bot_user_id: int) -> None:
    """Sync helper to run one market maker cycle in a separate thread."""
    db = SessionLocal()
    try:
        bot = db.query(User).filter(User.user_id == bot_user_id).first()
        if not bot:
            logger.error("Bot user was deleted; restarting.")
            return

        stocks = db.query(Stock).all()
        for stock in stocks:
            try:
                mid_price = _get_mid_price(db, stock)
                if mid_price is None:
                    logger.debug(f"Skipping stock {stock.symbol}: no mid price yet")
                    continue

                cancelled = _cancel_stale_quotes(db, bot.user_id, stock.stock_id, mid_price)
                if cancelled > 0:
                    logger.debug(f"Bot: cancelled {cancelled} stale orders for {stock.symbol}")

                _place_bot_quotes(db, bot, stock)

            except Exception as e:
                logger.error(f"Market maker error for stock {stock.symbol}: {e}")
                db.rollback()

        db.commit()
    except Exception as e:
        logger.error(f"Market maker cycle error: {e}")
        db.rollback()
    finally:
        db.close()


async def market_maker() -> None:
    """
    Background task: run the market maker bots.

    Every BOT_QUOTE_REFRESH_INTERVAL seconds:
    1. For each stock:
       a. Cancel stale quotes (orders > 2% away from mid)
       b. Place fresh bid/ask pair around mid-price

    Runs indefinitely as a background task in the app lifespan.
    """
    try:
        bot_user_id = await asyncio.to_thread(_init_bot_user)
        logger.info(f"Market maker started with bot user_id={bot_user_id}")
    except Exception as e:
        logger.error(f"Failed to initialize market maker: {e}")
        return

    while True:
        await asyncio.to_thread(_run_market_maker_cycle, bot_user_id)
        await asyncio.sleep(BOT_QUOTE_REFRESH_INTERVAL)

