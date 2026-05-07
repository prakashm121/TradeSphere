from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # Hashed password
    balance = Column(Float, default=50000.0)
    margin_held = Column(Float, default=0.0)  # collateral locked for open shorts
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    last_recovery_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user")
    portfolio_items = relationship("Portfolio", back_populates="user")

    @property
    def available_cash(self) -> float:
        return float(self.balance or 0.0) - float(self.margin_held or 0.0)

