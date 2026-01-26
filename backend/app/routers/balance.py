from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/balance", tags=["balance"])


@router.get("")
def get_balance(current_user: User = Depends(get_current_user)):
    """Get current user's balance."""
    return {"balance": current_user.balance}


@router.post("/recover")
def recover_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Recover balance (once per 24 hours)."""
    now = datetime.utcnow()
    
    if current_user.last_recovery_date:
        last_recovery_date = current_user.last_recovery_date
        if isinstance(last_recovery_date, str):
            last_recovery_date = datetime.fromisoformat(last_recovery_date)
        
        time_diff = now - last_recovery_date
        if time_diff < timedelta(hours=24):
            time_left = timedelta(hours=24) - time_diff
            hours_left = int(time_left.total_seconds() // 3600)
            minutes_left = int((time_left.total_seconds() % 3600) // 60)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Recovery available in {hours_left}h {minutes_left}m"
            )
    
    recovery_amount = 5000
    current_user.balance += recovery_amount
    current_user.last_recovery_date = now
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "success": True,
        "recovery_amount": recovery_amount,
        "new_balance": current_user.balance
    }


@router.get("/recovery-status")
def recovery_status(current_user: User = Depends(get_current_user)):
    """Check recovery status."""
    if not current_user.last_recovery_date:
        return {"can_recover": True}
    
    last_recovery_date = current_user.last_recovery_date
    if isinstance(last_recovery_date, str):
        last_recovery_date = datetime.fromisoformat(last_recovery_date)
    
    now = datetime.utcnow()
    time_diff = now - last_recovery_date
    
    if time_diff >= timedelta(hours=24):
        return {"can_recover": True}
    
    time_left = timedelta(hours=24) - time_diff
    hours_left = int(time_left.total_seconds() // 3600)
    minutes_left = int((time_left.total_seconds() % 3600) // 60)
    
    return {
        "can_recover": False,
        "hours_left": hours_left,
        "minutes_left": minutes_left
    }

