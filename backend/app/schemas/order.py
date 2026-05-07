from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


Side = Literal["BUY", "SELL"]
OrderType = Literal["MARKET", "LIMIT"]
OrderStatus = Literal["OPEN", "PARTIAL", "FILLED", "CANCELLED"]


class OrderRequest(BaseModel):
    stock_id: int = Field(..., gt=0)
    side: Side
    order_type: OrderType
    quantity: int = Field(..., gt=0)
    price: Optional[float] = Field(default=None, gt=0)


class OrderResponse(BaseModel):
    id: int
    stock_id: int
    side: Side
    order_type: OrderType
    quantity: int
    remaining_qty: int
    price: Optional[float]
    status: OrderStatus
    created_at: datetime

    class Config:
        from_attributes = True


class PlaceOrderResult(BaseModel):
    order: OrderResponse
    fills: int
    filled_qty: int
    avg_fill_price: Optional[float] = None
    new_balance: float
    available_cash: float


class BookLevel(BaseModel):
    price: float
    quantity: int


class BookSnapshot(BaseModel):
    stock_id: int
    bids: list[BookLevel]
    asks: list[BookLevel]
