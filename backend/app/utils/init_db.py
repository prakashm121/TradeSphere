from sqlalchemy.orm import Session
from app.core.database import engine, Base
from app.models.user import User
from app.models.stock import Stock
from app.models.transaction import Transaction
from app.models.portfolio import Portfolio


def init_database():
    """Initialize database tables and seed initial data."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Seed stocks
    from app.core.database import SessionLocal
    db = SessionLocal()
    
    try:
        # Check if stocks already exist
        existing_stocks = db.query(Stock).count()
        if existing_stocks > 0:
            return
        
        stocks_data = [
            ("Apple Inc.", "AAPL", 150.00),
            ("Google", "GOOGL", 2800.00),
            ("Microsoft", "MSFT", 300.00),
            ("Amazon", "AMZN", 3200.00),
            ("Tesla", "TSLA", 800.00),
            ("Meta Platforms", "META", 250.00),
            ("Netflix", "NFLX", 400.00),
            ("NVIDIA", "NVDA", 900.00),
            ("Reliance Industries", "RELIANCE", 2500.00),
            ("Tata Consultancy Services", "TCS", 3500.00),
            ("Infosys Ltd.", "INFY", 1533.40),
            ("Wipro Ltd.", "WIPRO", 254.15),
            ("HDFC Bank Ltd.", "HDFCBANK", 1700.00),
            ("ICICI Bank Ltd.", "ICICIBANK", 1050.00),
            ("Hindustan Unilever Ltd.", "HUL", 2700.00),
            ("Bharti Airtel Ltd.", "BHARTIARTL", 1050.00),
            ("ITC Ltd.", "ITC", 460.00),
            ("State Bank of India", "SBIN", 700.00),
            ("Larsen & Toubro", "LT", 3500.00),
            ("Maruti Suzuki India", "MARUTI", 900.00),
            ("HCL Technologies", "HCLTECH", 1500.00),
            ("Kotak Mahindra Bank", "KOTAKBANK", 1800.00),
        ]
        
        for name, symbol, price in stocks_data:
            stock = Stock(name=name, symbol=symbol, price=price)
            db.add(stock)
        
        db.commit()
    finally:
        db.close()

