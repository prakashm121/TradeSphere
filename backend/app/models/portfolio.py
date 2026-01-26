from sqlalchemy import Column, Integer, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class Portfolio(Base):
    __tablename__ = "portfolio"
    
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.stock_id"), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'stock_id'),
    )
    
    # Relationships
    user = relationship("User", back_populates="portfolio_items")
    stock = relationship("Stock", back_populates="portfolio_items")

