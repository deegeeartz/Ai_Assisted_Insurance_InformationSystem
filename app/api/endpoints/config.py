from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.core import User, UserRole, PlatformConfig
from app.services.auth import get_current_user
import redis
import os

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


async def _require_insurer_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Only insurers and superadmins can manage policy config."""
    if current_user.role not in (UserRole.ADMIN, UserRole.INSURER):
        raise HTTPException(status_code=403, detail="Admin or insurer access required.")
    return current_user


class PolicyPrefixUpdate(BaseModel):
    product_type: str
    prefix: str

@router.get("/policy/prefixes")
async def get_policy_prefixes(
    current_user: User = Depends(_require_insurer_or_admin),
):
    """Get all configured policy prefixes."""
    # This is a bit inefficient (KEYS *) but fine for a hackathon with few products
    keys = redis_client.keys("config:policy:prefix:*")
    configs = {}
    for key in keys:
        product_type = key.split(":")[-1]
        configs[product_type] = redis_client.get(key)
    
    # Ensure defaults are included if not set
    defaults = ["life_basic", "auto_comprehensive", "gadget_protection"]
    for p in defaults:
        if p not in configs:
            configs[p] = "IB"
            
    return configs

@router.post("/policy/prefixes")
async def update_policy_prefix(
    update: PolicyPrefixUpdate,
    current_user: User = Depends(_require_insurer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update the policy prefix for a product."""
    key = f"config:policy:prefix:{update.product_type}"
    redis_client.set(key, update.prefix)
    
    from app.models.audit import AuditLog
    db.add(AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="update_policy_prefix",
        resource_type="redis_config",
        resource_id=key,
        details=f"new_prefix: {update.prefix}",
    ))
    await db.commit()
    
    return {"message": "Prefix updated", "product": update.product_type, "new_prefix": update.prefix}

