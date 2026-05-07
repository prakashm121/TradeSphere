from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.schemas.trade import TradeRequest, TradeResponse
from app.services.trade_service import TradeService

router = APIRouter(prefix="/trades", tags=["trades"])


@router.post("/buy", response_model=TradeResponse)
def buy_stock(
    trade_data: TradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Buy stocks."""
    return TradeService.execute_trade(db, current_user.user_id, trade_data, "BUY")


@router.post("/sell", response_model=TradeResponse)
def sell_stock(
    trade_data: TradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sell stocks."""
    return TradeService.execute_trade(db, current_user.user_id, trade_data, "SELL")
