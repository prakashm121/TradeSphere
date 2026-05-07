from sqlalchemy import Column, Integer, BigInteger, Float, DateTime, String, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func

from app.core.database import Base


class Candle(Base):
    __tablename__ = "candles"

    id = Column(BigInteger, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.stock_id"), nullable=False, index=True)
    resolution = Column(String(3), nullable=False)  # 1m | 5m | 1h
    open_time = Column(DateTime(timezone=True), nullable=False, index=True)

    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("stock_id", "resolution", "open_time", name="uq_candles_stock_res_open_time"),
        Index("ix_candles_stock_res_open_time_desc", "stock_id", "resolution", "open_time"),
    )
