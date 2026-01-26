from pydantic import BaseModel, Field
from typing import Optional


class TradeRequest(BaseModel):
    stock_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class TradeResponse(BaseModel):
    success: bool
    new_balance: float


class StockResponse(BaseModel):
    stock_id: int
    name: str
    symbol: str
    price: float
    
    class Config:
        from_attributes = True


class PortfolioItem(BaseModel):
    quantity: int
    name: str
    symbol: str
    price: float
    stock_id: int
    current_value: float
    
    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    transaction_id: int
    user_id: int
    stock_id: int
    type: str
    quantity: int
    price_at_transaction: float
    timestamp: str
    name: Optional[str] = None
    symbol: Optional[str] = None
    
    class Config:
        from_attributes = True

