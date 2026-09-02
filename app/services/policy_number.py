import redis.asyncio as redis
import os
from datetime import datetime

# Redis connection for atomic counters
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


async def generate_policy_number(
    product_type: str,
    prefix: str = "IB",
    sequence_length: int = 6,
) -> str:
    """
    Generate a unique policy number using Redis atomic counters.
    
    Format: {PREFIX}-{PRODUCT}-{YYYY}-{SEQ}
    Example: IB-LIFE-2026-000001
    """
    # Fetch prefix from Redis configuration or default to "IB"
    config_key = f"config:policy:prefix:{product_type}"
    start_time = datetime.now() 
    # Try to get custom prefix, with a short timeout/fallback if Redis is slow (though strictly redis is fast)
    try:
        custom_prefix = await redis_client.get(config_key)
        if custom_prefix:
            prefix = custom_prefix
    except Exception:
        pass # Fallback to default "IB"

    year = datetime.now().strftime("%Y")
    counter_key = f"policy_seq:{prefix}:{product_type}:{year}"

    # Redis INCR is atomic - safe for concurrent requests
    seq = await redis_client.incr(counter_key)

    # Format with zero-padding
    seq_str = str(seq).zfill(sequence_length)

    return f"{prefix}-{product_type.upper()}-{year}-{seq_str}"
