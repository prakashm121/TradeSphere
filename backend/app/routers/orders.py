from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.schemas.order import OrderRequest, PlaceOrderResult
from app.services.trade_service import TradeService


router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=PlaceOrderResult, status_code=status.HTTP_201_CREATED)
def place_order(
    req: OrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.order_type == "LIMIT" and req.price is None:
        raise HTTPException(status_code=400, detail="LIMIT orders require price")

    incoming, fills, user = TradeService.place_order(
        db=db,
        user_id=current_user.user_id,
        stock_id=req.stock_id,
        side=req.side,
        order_type=req.order_type,
        quantity=req.quantity,
        price=req.price,
    )

    filled_qty = req.quantity - int(incoming.remaining_qty)
    avg_fill = None
    if fills:
        notional = sum(f.price * f.quantity for f in fills)
        qty = sum(f.quantity for f in fills)
        avg_fill = (notional / qty) if qty else None

    return {
        "order": incoming,
        "fills": len(fills),
        "filled_qty": filled_qty,
        "avg_fill_price": avg_fill,
        "new_balance": float(user.balance),
        "available_cash": float(user.available_cash),
    }
