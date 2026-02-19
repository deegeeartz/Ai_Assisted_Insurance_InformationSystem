from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
import redis
import os

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

class PolicyPrefixUpdate(BaseModel):
    product_type: str
    prefix: str

@router.get("/policy/prefixes")
async def get_policy_prefixes():
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
async def update_policy_prefix(update: PolicyPrefixUpdate):
    """Update the policy prefix for a product."""
    key = f"config:policy:prefix:{update.product_type}"
    redis_client.set(key, update.prefix)
    return {"message": "Prefix updated", "product": update.product_type, "new_prefix": update.prefix}
