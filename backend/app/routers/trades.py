from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.stock import Stock
from app.models.transaction import Transaction
from app.models.portfolio import Portfolio
from app.schemas.trade import TradeRequest, TradeResponse

router = APIRouter(prefix="/trades", tags=["trades"])


@router.post("/buy", response_model=TradeResponse)
def buy_stock(
    trade_data: TradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Buy stocks."""
    if trade_data.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be positive"
        )
    
    # Get stock
    stock = db.query(Stock).filter(Stock.stock_id == trade_data.stock_id).first()
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found"
        )
    
    # Calculate total cost
    total_cost = stock.price * trade_data.quantity
    
    # Check balance
    if current_user.balance < total_cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )
    
    # Update user balance
    current_user.balance -= total_cost
    
    # Create transaction
    transaction = Transaction(
        user_id=current_user.user_id,
        stock_id=stock.stock_id,
        type="BUY",
        quantity=trade_data.quantity,
        price_at_transaction=stock.price,
        timestamp=datetime.utcnow()
    )
    db.add(transaction)
    
    # Update portfolio
    portfolio_item = db.query(Portfolio).filter(
        Portfolio.user_id == current_user.user_id,
        Portfolio.stock_id == stock.stock_id
    ).first()
    
    if portfolio_item:
        portfolio_item.quantity += trade_data.quantity
    else:
        portfolio_item = Portfolio(
            user_id=current_user.user_id,
            stock_id=stock.stock_id,
            quantity=trade_data.quantity
        )
        db.add(portfolio_item)
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "success": True,
        "new_balance": current_user.balance
    }


@router.post("/sell", response_model=TradeResponse)
def sell_stock(
    trade_data: TradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sell stocks."""
    if trade_data.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be positive"
        )
    
    # Get portfolio holding
    portfolio_item = db.query(Portfolio).filter(
        Portfolio.user_id == current_user.user_id,
        Portfolio.stock_id == trade_data.stock_id
    ).first()
    
    if not portfolio_item or portfolio_item.quantity < trade_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient shares"
        )
    
    # Get stock
    stock = db.query(Stock).filter(Stock.stock_id == trade_data.stock_id).first()
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found"
        )
    
    # Calculate total value
    total_value = stock.price * trade_data.quantity
    
    # Update user balance
    current_user.balance += total_value
    
    # Create transaction
    transaction = Transaction(
        user_id=current_user.user_id,
        stock_id=stock.stock_id,
        type="SELL",
        quantity=trade_data.quantity,
        price_at_transaction=stock.price,
        timestamp=datetime.utcnow()
    )
    db.add(transaction)
    
    # Update portfolio
    portfolio_item.quantity -= trade_data.quantity
    if portfolio_item.quantity == 0:
        db.delete(portfolio_item)
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "success": True,
        "new_balance": current_user.balance
    }

