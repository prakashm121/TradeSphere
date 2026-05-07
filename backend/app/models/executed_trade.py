from sqlalchemy import Column, Integer, BigInteger, Float, DateTime, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ExecutedTrade(Base):
    __tablename__ = "executed_trades"

    id = Column(BigInteger, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.stock_id"), nullable=False, index=True)

    buy_order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=True)
    sell_order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=True)

    buyer_id = Column(Integer, ForeignKey("users.user_id"), nullable=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.user_id"), nullable=True, index=True)

    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    aggressor_side = Column(String(4), nullable=False)  # BUY | SELL

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    stock = relationship("Stock")
    buyer = relationship("User", foreign_keys=[buyer_id])
    seller = relationship("User", foreign_keys=[seller_id])


Index("ix_executed_trades_stock_ts", ExecutedTrade.stock_id, ExecutedTrade.timestamp)
