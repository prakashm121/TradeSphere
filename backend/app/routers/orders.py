from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.order import Order
from app.schemas.order import OrderRequest, OrderResponse, PlaceOrderResult
from app.services.trade_service import TradeService
from app.routers.websocket import emit_price_update, emit_trade_tick, emit_book_snapshot


router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=PlaceOrderResult, status_code=status.HTTP_201_CREATED)
def place_order(
    req: OrderRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Place a new BUY or SELL order (MARKET or LIMIT type)."""
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

    for fill in fills:
        background_tasks.add_task(
            emit_trade_tick,
            req.stock_id,
            float(fill.price),
            int(fill.quantity),
            fill.aggressor_side,
        )

    background_tasks.add_task(emit_price_update, req.stock_id)
    background_tasks.add_task(emit_book_snapshot, req.stock_id)

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


@router.get("", response_model=List[OrderResponse])
def get_user_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all orders for the current user (open, partial, and recent fills)."""
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.user_id)
        .order_by(Order.created_at.desc())
        .limit(100)  # Last 100 orders
        .all()
    )
    return [OrderResponse.model_validate(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific order."""
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.user_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return OrderResponse.model_validate(order)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel a resting limit order. Market orders cannot be cancelled (already filled or rejected)."""
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.user_id)
        .with_for_update()
        .first()
    )
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    if order.status in ("FILLED", "CANCELLED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status {order.status}",
        )
    
    # If partially filled, canceling leaves the filled part as-is and cancels remaining
    order.status = "CANCELLED"
    order.updated_at = datetime.utcnow()
    
    db.commit()
    return None
