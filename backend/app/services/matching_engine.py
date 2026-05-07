from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal

from sqlalchemy.orm import Session

from app.models.order import Order


Side = Literal["BUY", "SELL"]


@dataclass(frozen=True)
class Fill:
    price: float
    quantity: int
    aggressor_side: Side
    resting_order_id: int
    resting_user_id: int


class MatchingEngine:
    """
    Pure matching logic. Must be called inside an existing DB transaction.
    Assumes the caller will insert/lock the incoming Order row.
    """

    @staticmethod
    def match(db: Session, incoming: Order) -> list[Fill]:
        if incoming.remaining_qty <= 0:
            return []

        if incoming.side not in ("BUY", "SELL"):
            raise ValueError("Invalid side")
        if incoming.order_type not in ("MARKET", "LIMIT"):
            raise ValueError("Invalid order_type")
        if incoming.order_type == "LIMIT" and (incoming.price is None or incoming.price <= 0):
            raise ValueError("LIMIT orders require price")

        opposite_side: Side = "SELL" if incoming.side == "BUY" else "BUY"

        q = (
            db.query(Order)
            .filter(
                Order.stock_id == incoming.stock_id,
                Order.side == opposite_side,
                Order.status.in_(("OPEN", "PARTIAL")),
                Order.user_id != incoming.user_id,  # self-trade prevention
            )
        )

        # Price-time priority
        if incoming.side == "BUY":
            q = q.order_by(Order.price.asc(), Order.created_at.asc())
        else:
            q = q.order_by(Order.price.desc(), Order.created_at.asc())

        # Lock only the resting rows we may match against
        resting_orders: list[Order] = q.with_for_update().all()

        fills: list[Fill] = []
        remaining = int(incoming.remaining_qty)

        for resting in resting_orders:
            if remaining <= 0:
                break
            if resting.remaining_qty <= 0:
                continue
            if resting.price is None:
                # Resting orders should always be LIMIT; skip if bad data.
                continue

            # Limit price checks (incoming price is a constraint)
            if incoming.order_type == "LIMIT":
                if incoming.side == "BUY" and resting.price > float(incoming.price):
                    break  # asks are sorted low->high; no further matches possible
                if incoming.side == "SELL" and resting.price < float(incoming.price):
                    break  # bids are sorted high->low; no further matches possible

            fill_qty = min(remaining, int(resting.remaining_qty))
            fill_price = float(resting.price)  # resting sets price

            fills.append(
                Fill(
                    price=fill_price,
                    quantity=fill_qty,
                    aggressor_side=incoming.side,
                    resting_order_id=int(resting.id),
                    resting_user_id=int(resting.user_id),
                )
            )

            # Update resting order state
            resting.remaining_qty -= fill_qty
            resting.status = "FILLED" if resting.remaining_qty == 0 else "PARTIAL"

            remaining -= fill_qty

        incoming.remaining_qty = remaining

        # Status update rules
        if incoming.remaining_qty == 0:
            incoming.status = "FILLED"
        else:
            if incoming.order_type == "MARKET":
                # Market orders never rest
                incoming.status = "CANCELLED"
            else:
                incoming.status = "OPEN"

        return fills
