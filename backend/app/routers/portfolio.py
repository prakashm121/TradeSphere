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
    """Get user's portfolio (includes long and short positions)."""
    portfolio_items = db.query(Portfolio).filter(
        Portfolio.user_id == current_user.user_id,
        Portfolio.quantity != 0
    ).all()
    
    result = []
    for item in portfolio_items:
        stock = item.stock
        current_value = item.quantity * stock.price
        avg_entry_price = item.avg_entry_price or 0.0
        unrealised_pnl = (stock.price - avg_entry_price) * item.quantity
        position_type = "LONG" if item.quantity >= 0 else "SHORT"

        result.append({
            "quantity": item.quantity,
            "name": stock.name,
            "symbol": stock.symbol,
            "price": stock.price,
            "stock_id": stock.stock_id,
            "current_value": current_value,
            "avg_entry_price": avg_entry_price,
            "margin_held": item.margin_held,
            "position_type": position_type,
            "unrealised_pnl": unrealised_pnl,
        })
    
    return result

