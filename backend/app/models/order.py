from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.stock_id"), nullable=False, index=True)

    side = Column(String(4), nullable=False)  # BUY | SELL
    order_type = Column(String(6), nullable=False)  # MARKET | LIMIT

    quantity = Column(Integer, nullable=False)
    remaining_qty = Column(Integer, nullable=False)
    price = Column(Float, nullable=True)  # null for market orders
    status = Column(String(9), nullable=False, default="OPEN")  # OPEN | PARTIAL | FILLED | CANCELLED

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", backref="orders")
    stock = relationship("Stock", backref="orders")


Index("ix_orders_match", Order.stock_id, Order.side, Order.price, Order.created_at)
