from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.auth import get_current_user
from app.models.core import User, Policy, SLARecord, UserRole
from app.models.manual import UnderwritingManual

router = APIRouter()

@router.get("/audit-log")
def get_audit_log(
    skip: int = 0, 
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get chronological list of underwriting decisions.
    For MVP, we use Policy records as 'decisions'.
    In prod, this would be a separate immutable Ledger table.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.INSURER]:
        raise HTTPException(status_code=403, detail="Not authorized")

    policies = db.query(Policy).order_by(Policy.created_at.desc()).offset(skip).limit(limit).all()
    
    audit_trail = []
    for p in policies:
        audit_trail.append({
            "timestamp": p.created_at,
            "policy_number": p.policy_number,
            "product_type": p.product_type,
            "premium": p.premium_amount,
            "status": p.status,
            "customer_email": p.user.email if p.user else "N/A"
        })
        
    return audit_trail

@router.get("/rules/inspector")
def inspect_rules(
    manual_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """View the extracted logic (JSON) for a specific manual"""
    if current_user.role not in [UserRole.ADMIN, UserRole.INSURER]:
        raise HTTPException(status_code=403, detail="Not authorized")

    if manual_id:
        manual = db.query(UnderwritingManual).filter(UnderwritingManual.id == manual_id).first()
        if not manual:
            raise HTTPException(status_code=404, detail="Manual not found")
        return {"id": manual.id, "filename": manual.filename, "rules": manual.compiled_rules}
    
    # List all manuals
    manuals = db.query(UnderwritingManual).all()
    return [{"id": m.id, "filename": m.filename, "uploaded_at": m.upload_date} for m in manuals]

@router.get("/sla/breaches")
def get_sla_breaches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of policies that missed their SLA"""
    if current_user.role not in [UserRole.ADMIN, UserRole.INSURER]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    breaches = db.query(SLARecord).filter(SLARecord.status == "breached").all()
    return breaches
