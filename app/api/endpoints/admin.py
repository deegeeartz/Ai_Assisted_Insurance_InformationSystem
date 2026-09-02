from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict

from app.db.session import get_db
from app.models.core import User, UserRole, Policy, Payment
from app.services.auth import get_current_user

router = APIRouter()

async def get_superadmin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure the user is a superadmin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Superadmin access required.")
    return current_user

@router.get("/metrics", response_model=Dict)
async def get_global_metrics(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_superadmin)
):
    """
    Tier 1 Superadmin API: Global Observability across all tenants.
    """
    # 1. Total Gross Written Premium
    gwp_query = await db.execute(select(func.sum(Policy.premium_annual)).where(Policy.status == "active"))
    total_gwp = gwp_query.scalar() or 0.0
    
    # 2. Total active policies
    policies_query = await db.execute(select(func.count(Policy.id)).where(Policy.status == "active"))
    total_policies = policies_query.scalar() or 0
    
    # 3. Tenants (Insurers) and Partners counts
    users_query = await db.execute(select(User.role, func.count(User.id)).group_by(User.role))
    user_counts = {role: count for role, count in users_query.all()}
    
    return {
        "gross_written_premium": total_gwp,
        "total_active_policies": total_policies,
        "active_insurers": user_counts.get("insurer", 0),
        "active_partners": user_counts.get("partner", 0),
        "total_consumers": user_counts.get("consumer", 0)
    }

@router.get("/tenants", response_model=List[Dict])
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_superadmin)
):
    """
    Returns all registered insurer tenants and their status.
    """
    query = await db.execute(select(User).where(User.role == UserRole.INSURER))
    insurers = query.scalars().all()
    
    results = []
    for insurer in insurers:
        # Get policy count for this tenant
        pol_q = await db.execute(select(func.count(Policy.id)).where(Policy.tenant_id == insurer.tenant_id))
        pol_count = pol_q.scalar() or 0
        
        results.append({
            "id": insurer.id,
            "company_name": insurer.company_name,
            "tenant_id": insurer.tenant_id,
            "email": insurer.email,
            "is_active": insurer.is_active,
            "total_policies": pol_count
        })
    return results

@router.post("/tenants/{tenant_id}/suspend")
async def toggle_tenant_status(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_superadmin)
):
    """
    God-Mode Kill Switch (Tenant Level): Suspends a tenant account, preventing all API underwriting for their products.
    """
    query = await db.execute(select(User).where(User.tenant_id == tenant_id, User.role == UserRole.INSURER))
    tenant = query.scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
        
    tenant.is_active = not tenant.is_active
    
    from app.models.audit import AuditLog
    db.add(AuditLog(
        user_id=admin.id,
        user_email=admin.email,
        action="suspend_tenant" if not tenant.is_active else "unsuspend_tenant",
        resource_type="tenant",
        resource_id=tenant_id,
    ))

    await db.commit()
    return {"message": f"Tenant {tenant.company_name} active status set to {tenant.is_active}", "is_active": tenant.is_active}


from app.models.core import PlatformConfig
from pydantic import BaseModel

class ConfigUpdate(BaseModel):
    value: str

@router.get("/config")
async def get_platform_configs(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_superadmin)
):
    """View global platform configurations (Kill Switch, Commission Rates, etc)."""
    query = await db.execute(select(PlatformConfig))
    return query.scalars().all()

@router.put("/config/{key}")
async def update_platform_config(
    key: str,
    payload: ConfigUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_superadmin)
):
    """Update a specific global config (e.g. set kill_switch to 'true')."""
    query = await db.execute(select(PlatformConfig).where(PlatformConfig.key == key))
    config = query.scalars().first()
    if not config:
        raise HTTPException(status_code=404, detail="Config key not found")
    
    old_value = config.value
    config.value = payload.value
    
    from app.models.audit import AuditLog
    db.add(AuditLog(
        user_id=admin.id,
        user_email=admin.email,
        action="update_config",
        resource_type="config",
        resource_id=key,
        details=f"old_value: {old_value}, new_value: {payload.value}",
    ))

    await db.commit()
    return {"message": f"Config {key} updated", "new_value": config.value}
