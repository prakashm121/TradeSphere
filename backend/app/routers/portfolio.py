from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.portfolio import Portfolio
from app.schemas.trade import PortfolioItem

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=list[PortfolioItem])
def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's portfolio."""
    portfolio_items = db.query(Portfolio).filter(
        Portfolio.user_id == current_user.user_id,
        Portfolio.quantity > 0
    ).all()
    
    result = []
    for item in portfolio_items:
        stock = item.stock
        result.append({
            "quantity": item.quantity,
            "name": stock.name,
            "symbol": stock.symbol,
            "price": stock.price,
            "stock_id": stock.stock_id,
            "current_value": item.quantity * stock.price
        })
    
    return result

