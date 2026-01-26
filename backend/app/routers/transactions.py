from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.trade import TransactionResponse

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionResponse])
def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get user's transaction history."""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.user_id
    ).order_by(Transaction.timestamp.desc()).limit(limit).all()
    
    result = []
    for transaction in transactions:
        result.append({
            "transaction_id": transaction.transaction_id,
            "user_id": transaction.user_id,
            "stock_id": transaction.stock_id,
            "type": transaction.type,
            "quantity": transaction.quantity,
            "price_at_transaction": transaction.price_at_transaction,
            "timestamp": transaction.timestamp.isoformat(),
            "name": transaction.stock.name,
            "symbol": transaction.stock.symbol
        })
    
    return result

