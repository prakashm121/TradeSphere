import logging
from app.core.database import SessionLocal
from app.models.user import User
from app.models.stock import Stock
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction
from app.schemas.trade import TradeRequest
from app.services.trade_service import TradeService

# Configure logging to see the logger output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_tests():
    db = SessionLocal()
    try:
        # 1. Setup - Create a test user and test stock
        print("Setting up test data...")
        test_email = "test_trade_service@example.com"
        user = db.query(User).filter(User.email == test_email).first()
        if not user:
            user = User(
                email=test_email,
                password="dummy_password",
                balance=100000.0,
                is_verified=True
            )
            db.add(user)
            
        test_stock_symbol = "TEST_TS"
        stock = db.query(Stock).filter(Stock.symbol == test_stock_symbol).first()
        if not stock:
            stock = Stock(name="Test Stock", symbol=test_stock_symbol, price=100.0)
            db.add(stock)
            
        db.commit()
        db.refresh(user)
        db.refresh(stock)
        
        user_id = user.user_id
        stock_id = stock.stock_id
        initial_price = stock.price
        
        print(f"Initial State: User Balance=${user.balance}, Stock Price=${initial_price}")
        
        # 2. Test BUY
        print("\n--- Testing BUY 10 shares ---")
        trade_req = TradeRequest(stock_id=stock_id, quantity=10)
        res = TradeService.execute_trade(db, user_id, trade_req, "BUY")
        
        db.refresh(stock)
        db.refresh(user)
        print(f"Buy Result: {res}")
        print(f"Post-Buy State: User Balance=${user.balance}, Stock Price=${stock.price}")
        
        assert user.balance < 100000.0, "Balance should have decreased"
        assert stock.price > initial_price, "Stock price should have increased due to buy impact"
        
        # 3. Test SELL
        print("\n--- Testing SELL 5 shares ---")
        trade_req_sell = TradeRequest(stock_id=stock_id, quantity=5)
        res_sell = TradeService.execute_trade(db, user_id, trade_req_sell, "SELL")
        
        db.refresh(stock)
        db.refresh(user)
        print(f"Sell Result: {res_sell}")
        print(f"Post-Sell State: User Balance=${user.balance}, Stock Price=${stock.price}")
        
        print("\nAll tests executed successfully. Trade logic is working.")

    except Exception as e:
        print(f"\nError during testing: {e}")
        db.rollback()
    finally:
        # Cleanup
        if 'user' in locals() and user:
            # Delete transactions and portfolio
            db.query(Transaction).filter(Transaction.user_id == user.user_id).delete()
            db.query(Portfolio).filter(Portfolio.user_id == user.user_id).delete()
            db.query(User).filter(User.user_id == user.user_id).delete()
            db.query(Stock).filter(Stock.symbol == "TEST_TS").delete()
            db.commit()
        db.close()

if __name__ == "__main__":
    run_tests()
