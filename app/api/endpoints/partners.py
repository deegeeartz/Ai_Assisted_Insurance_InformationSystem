from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.auth import get_current_user
from app.models.core import User, Policy, Payment, UserRole

router = APIRouter()

@router.get("/dashboard")
def get_partner_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get aggregated metrics for the partner:
    - Total Policies Sold
    - Total Commission Earned
    - Recent Transactions
    """
    if current_user.role != UserRole.PARTNER:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Metrics
    policies = db.query(Policy).filter(Policy.partner_id == current_user.id).all()
    total_policies = len(policies)
    
    # Calculate commission from payments linked to these policies
    # This is a simplified aggregation. In prod, use SQL func.sum()
    total_commission = 0
    recent_transactions = []
    
    for policy in policies:
        for payment in policy.payments:
            if payment.status == "success":
                total_commission += payment.partner_commission
                recent_transactions.append({
                    "policy_id": policy.policy_number,
                    "amount": payment.amount,
                    "commission": payment.partner_commission,
                    "date": payment.payment_date
                })

    # Sort transactions by date desc
    recent_transactions.sort(key=lambda x: x['date'], reverse=True)

    return {
        "metrics": {
            "total_policies_sold": total_policies,
            "total_commission_earned": round(total_commission, 2),
            "currency": "NGN"
        },
        "recent_transactions": recent_transactions[:10],
        "api_key": current_user.api_key  # For display in portal
    }

@router.post("/api-key/rotate")
def rotate_api_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate the Partner's API Key"""
    if current_user.role != UserRole.PARTNER:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    import secrets
    new_key = f"ib_sk_{secrets.token_urlsafe(32)}"
    current_user.api_key = new_key
    db.commit()
    
    return {"api_key": new_key}
