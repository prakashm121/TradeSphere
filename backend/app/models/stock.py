from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class Stock(Base):
    __tablename__ = "stocks"
    
    stock_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    symbol = Column(String, unique=True, index=True, nullable=False)
    price = Column(Float, nullable=False)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="stock")
    portfolio_items = relationship("Portfolio", back_populates="stock")

