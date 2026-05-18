import asyncio
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
from app.models.user import User
from app.models.stock import Stock
from app.models.transaction import Transaction
from app.models.portfolio import Portfolio
from app.models.order import Order
from app.models.executed_trade import ExecutedTrade
from app.models.trade_history import TradeHistory
from app.schemas.trade import TradeRequest
from app.services.matching_engine import MatchingEngine, Fill
from app.routers.websocket import emit_price_update, emit_trade_tick, emit_book_snapshot, emit_order_update

logger = logging.getLogger(__name__)

class TradeService:
    """
    V2 trade engine: prices move only when orders match.

    For backward compatibility, execute_trade() maps to a MARKET order and records
    Transaction rows for both counterparties per fill (so /transactions keeps working).
    """

    @staticmethod
    def _get_or_create_position(db: Session, user_id: int, stock_id: int) -> Portfolio:
        pos = (
            db.query(Portfolio)
            .filter(Portfolio.user_id == user_id, Portfolio.stock_id == stock_id)
            .with_for_update()
            .first()
        )
        if pos:
            return pos
        pos = Portfolio(user_id=user_id, stock_id=stock_id, quantity=0, avg_entry_price=0.0, margin_held=0.0)
        db.add(pos)
        return pos

    @staticmethod
    def _lock_users(db: Session, user_ids: list[int]) -> list[User]:
        # lock in stable order to avoid deadlocks
        ids = sorted(set(int(x) for x in user_ids))
        return (
            db.query(User)
            .filter(User.user_id.in_(ids))
            .order_by(User.user_id.asc())
            .with_for_update()
            .all()
        )

    @staticmethod
    def _apply_fill(
        db: Session,
        stock: Stock,
        incoming_order: Order,
        fill: Fill,
    ) -> None:
        # Determine buyer/seller by aggressor side
        if incoming_order.side == "BUY":
            buyer_id = incoming_order.user_id
            seller_id = fill.resting_user_id
            buy_order_id = incoming_order.id
            sell_order_id = fill.resting_order_id
        else:
            buyer_id = fill.resting_user_id
            seller_id = incoming_order.user_id
            buy_order_id = fill.resting_order_id
            sell_order_id = incoming_order.id

        users = TradeService._lock_users(db, [buyer_id, seller_id])
        user_map = {u.user_id: u for u in users}
        buyer = user_map[buyer_id]
        seller = user_map[seller_id]

        total = float(fill.price) * int(fill.quantity)

        # BUYER: debit cash (use available_cash so margin is respected)
        if buyer.available_cash < total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient available cash to fill order",
            )
        buyer.balance -= total

        # SELLER: credit cash (shorting margin handled by position logic below)
        seller.balance += total

        # Update portfolios (positions). We keep avg_entry_price + margin_held but for now
        # apply simple rules (full margin enforcement for increasing shorts).
        buyer_pos = TradeService._get_or_create_position(db, buyer_id, stock.stock_id)
        seller_pos = TradeService._get_or_create_position(db, seller_id, stock.stock_id)

        # Buyer receives shares
        TradeService._adjust_position_for_trade(
            db=db,
            user=buyer,
            pos=buyer_pos,
            side="BUY",
            qty=int(fill.quantity),
            price=float(fill.price),
        )

        # Seller delivers shares (may open/increase short)
        TradeService._adjust_position_for_trade(
            db=db,
            user=seller,
            pos=seller_pos,
            side="SELL",
            qty=int(fill.quantity),
            price=float(fill.price),
        )

        # Executed trade record
        db.add(
            ExecutedTrade(
                stock_id=stock.stock_id,
                buy_order_id=buy_order_id,
                sell_order_id=sell_order_id,
                buyer_id=buyer_id,
                seller_id=seller_id,
                price=float(fill.price),
                quantity=int(fill.quantity),
                aggressor_side=incoming_order.side,
            )
        )

        # Keep legacy transaction rows for history UI
        now = datetime.utcnow()
        db.add(
            Transaction(
                user_id=buyer_id,
                stock_id=stock.stock_id,
                type="BUY",
                quantity=int(fill.quantity),
                price_at_transaction=float(fill.price),
                timestamp=now,
            )
        )
        db.add(
            Transaction(
                user_id=seller_id,
                stock_id=stock.stock_id,
                type="SELL",
                quantity=int(fill.quantity),
                price_at_transaction=float(fill.price),
                timestamp=now,
            )
        )

        # Persist raw trade history so daily/weekly candle aggregation can use it.
        db.add(
            TradeHistory(
                stock_id=stock.stock_id,
                price=float(fill.price),
                quantity=int(fill.quantity),
                timestamp=now,
            )
        )

        # Price update: only fills move price
        stock.last_traded_price = float(fill.price)
        stock.price = float(fill.price)  # backward compat

    @staticmethod
    def _adjust_position_for_trade(db: Session, user: User, pos: Portfolio, side: str, qty: int, price: float) -> None:
        """
        Minimal v2 position accounting with margin for shorts:
        - qty > 0 means long, qty < 0 means short.
        - avg_entry_price tracks weighted average for the current side only.
        - margin_held is required at 100% notional for the short quantity.
        """
        if qty <= 0:
            return

        if side == "BUY":
            # If covering short, reduce short and release proportional margin
            if pos.quantity < 0:
                cover = min(qty, abs(pos.quantity))
                if abs(pos.quantity) > 0 and pos.margin_held > 0:
                    release = (pos.margin_held / abs(pos.quantity)) * cover
                    pos.margin_held -= release
                    user.margin_held -= release
                pos.quantity += cover  # less negative
                qty -= cover
                if pos.quantity == 0:
                    pos.avg_entry_price = 0.0
            # Remaining buy increases/opens long
            if qty > 0:
                if pos.quantity >= 0:
                    total_shares = pos.quantity + qty
                    if total_shares > 0:
                        pos.avg_entry_price = ((pos.avg_entry_price * pos.quantity) + (price * qty)) / total_shares
                    pos.quantity += qty
                else:
                    # flipped from short to long
                    pos.avg_entry_price = price
                    pos.quantity = qty
        else:
            # SELL reduces long first, then opens/increases short
            if pos.quantity > 0:
                sell_long = min(qty, pos.quantity)
                pos.quantity -= sell_long
                qty -= sell_long
                if pos.quantity == 0:
                    pos.avg_entry_price = 0.0

            if qty > 0:
                # Opening or increasing short requires margin = notional (100% paper margin)
                margin_required = price * qty
                if user.available_cash < margin_required:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient margin. Need {margin_required:.2f} to short {qty} shares.",
                    )
                # Update short avg entry price (weighted by absolute short size)
                current_short = abs(pos.quantity) if pos.quantity < 0 else 0
                total_short = current_short + qty
                if total_short > 0:
                    pos.avg_entry_price = ((pos.avg_entry_price * current_short) + (price * qty)) / total_short
                pos.quantity -= qty

                pos.margin_held += margin_required
                user.margin_held += margin_required

    @staticmethod
    def place_order(db: Session, user_id: int, stock_id: int, side: str, order_type: str, quantity: int, price: float | None):
        stock = db.query(Stock).filter(Stock.stock_id == stock_id).with_for_update().first()
        if not stock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")

        user = db.query(User).filter(User.user_id == user_id).with_for_update().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        incoming = Order(
            user_id=user_id,
            stock_id=stock_id,
            side=side,
            order_type=order_type,
            quantity=quantity,
            remaining_qty=quantity,
            price=price,
            status="OPEN",
        )
        db.add(incoming)
        db.flush()  # ensure incoming.id

        fills = MatchingEngine.match(db, incoming)
        for f in fills:
            TradeService._apply_fill(db, stock, incoming, f)

        # Ensure order status/remaining_qty updates are visible to subsequent queries
        db.flush()

        # Update bid/ask from top of book (best levels only)
        TradeService._update_best_prices(db, stock_id=stock.stock_id, stock=stock)

        db.flush()

        order_payload = {
            "order_id": int(incoming.id),
            "stock_id": int(incoming.stock_id),
            "status": incoming.status,
            "filled_qty": int(incoming.quantity - incoming.remaining_qty),
            "remaining_qty": int(incoming.remaining_qty),
            "order_type": incoming.order_type,
            "side": incoming.side,
            "price": float(incoming.price) if incoming.price is not None else None,
        }

        db.commit()

        TradeService._schedule_event_broadcast(stock.stock_id, fills, order_payload)

        db.refresh(user)
        db.refresh(incoming)
        return incoming, fills, user

    @staticmethod
    def _schedule_event_broadcast(stock_id: int, fills: list[Fill], incoming_order: dict) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        if fills:
            for fill in fills:
                loop.create_task(
                    emit_trade_tick(
                        stock_id=stock_id,
                        price=float(fill.price),
                        quantity=int(fill.quantity),
                        aggressor_side=fill.aggressor_side,
                    )
                )

        loop.create_task(emit_price_update(stock_id=stock_id))
        loop.create_task(emit_book_snapshot(stock_id=stock_id))
        loop.create_task(emit_order_update(incoming_order))

    @staticmethod
    def _update_best_prices(db: Session, stock_id: int, stock: Stock) -> None:
        best_bid = (
            db.query(Order.price)
            .filter(
                Order.stock_id == stock_id,
                Order.side == "BUY",
                Order.status.in_(("OPEN", "PARTIAL")),
                Order.remaining_qty > 0,
            )
            .order_by(Order.price.desc(), Order.created_at.asc())
            .limit(1)
            .scalar()
        )
        best_ask = (
            db.query(Order.price)
            .filter(
                Order.stock_id == stock_id,
                Order.side == "SELL",
                Order.status.in_(("OPEN", "PARTIAL")),
                Order.remaining_qty > 0,
            )
            .order_by(Order.price.asc(), Order.created_at.asc())
            .limit(1)
            .scalar()
        )
        stock.bid_price = float(best_bid) if best_bid is not None else None
        stock.ask_price = float(best_ask) if best_ask is not None else None

    @staticmethod
    def execute_trade(db: Session, user_id: int, trade_data: TradeRequest, trade_type: str):
        if trade_data.quantity <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be positive")

        side = "BUY" if trade_type == "BUY" else "SELL"
        # Legacy trades are market orders at best available price.
        incoming, fills, user = TradeService.place_order(
            db=db,
            user_id=user_id,
            stock_id=trade_data.stock_id,
            side=side,
            order_type="MARKET",
            quantity=int(trade_data.quantity),
            price=None,
        )

        return {
            "success": True,
            "new_balance": float(user.balance),
            "available_cash": float(user.available_cash),
        }
