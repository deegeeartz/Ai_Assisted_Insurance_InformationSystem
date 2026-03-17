from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.services.auth import get_current_user
from app.services.tenant import manual_tenant_from_product
from app.models.core import User, Policy, SLARecord, UserRole
from app.models.manual import UnderwritingManual

router = APIRouter()


def _is_admin(user: User) -> bool:
    role = user.role
    role_val = role.value if hasattr(role, "value") else str(role)
    return role_val == UserRole.ADMIN.value


def _tenant_scope(user: User) -> str:
    return user.tenant_id or user.email


def _manual_tenant(manual: UnderwritingManual) -> str:
    """Return the tenant for a manual, preferring the stored DB field."""
    return manual.tenant_id or manual_tenant_from_product(manual.product_type)

@router.get("/audit-log")
async def get_audit_log(
    skip: int = 0, 
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get chronological list of underwriting decisions.
    For MVP, we use Policy records as 'decisions'.
    In prod, this would be a separate immutable Ledger table.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.INSURER, UserRole.COMPLIANCE_OFFICER]:
        raise HTTPException(status_code=403, detail="Not authorized")

    query = select(Policy)
    if not _is_admin(current_user):
        query = query.where(Policy.tenant_id == _tenant_scope(current_user))

    result = await db.execute(
        query.order_by(Policy.bound_at.desc()).offset(skip).limit(limit)
    )
    policies = result.scalars().all()
    
    audit_trail = []
    for p in policies:
        audit_trail.append({
            "timestamp": p.bound_at,
            "policy_number": p.policy_number,
            "product_type": p.product_type,
            "premium": p.premium_annual,
            "status": p.status,
            "customer_email": p.holder_email
        })
        
    return audit_trail

@router.get("/rules/inspector")
async def inspect_rules(
    manual_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """View the extracted logic (JSON) for a specific manual"""
    if current_user.role not in [UserRole.ADMIN, UserRole.INSURER, UserRole.COMPLIANCE_OFFICER]:
        raise HTTPException(status_code=403, detail="Not authorized")

    tenant_scope = _tenant_scope(current_user)

    if manual_id:
        result = await db.execute(select(UnderwritingManual).where(UnderwritingManual.id == manual_id))
        manual = result.scalars().first()
        if not manual:
            raise HTTPException(status_code=404, detail="Manual not found")

        if not _is_admin(current_user) and _manual_tenant(manual) != tenant_scope:
            raise HTTPException(status_code=403, detail="Not authorized for this manual")

        return {"id": manual.id, "filename": manual.filename, "rules": manual.compiled_rules}
    
    # List all manuals
    result = await db.execute(select(UnderwritingManual))
    manuals = result.scalars().all()

    if not _is_admin(current_user):
        manuals = [m for m in manuals if _manual_tenant(m) == tenant_scope]

    return [{"id": m.id, "filename": m.filename, "uploaded_at": m.uploaded_at} for m in manuals]

@router.get("/sla/breaches")
async def get_sla_breaches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of policies that missed their SLA"""
    if current_user.role not in [UserRole.ADMIN, UserRole.INSURER, UserRole.COMPLIANCE_OFFICER]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    query = select(SLARecord).where(SLARecord.is_breached == True)
    if not _is_admin(current_user):
        query = query.where(SLARecord.tenant_id == _tenant_scope(current_user))

    result = await db.execute(query)
    breaches = result.scalars().all()
    return breaches
