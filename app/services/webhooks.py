import httpx
import hashlib
import hmac
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.core import WebhookConfig

logger = logging.getLogger(__name__)


async def dispatch_webhook(
    tenant_id: str,
    event_type: str,
    payload: dict,
    db: AsyncSession,
):
    """
    Dispatch webhook events to all registered URLs for a tenant.
    
    Events: policy.bound, payment.success, payment.failed, sla.breached
    """
    result = await db.execute(
        select(WebhookConfig)
        .where(WebhookConfig.tenant_id == tenant_id)
        .where(WebhookConfig.event_type == event_type)
        .where(WebhookConfig.is_active == True)
    )
    configs = result.scalars().all()

    for config in configs:
        try:
            body = json.dumps({
                "event": event_type,
                "data": payload,
            })

            headers = {"Content-Type": "application/json"}

            # HMAC signing if secret is configured
            if config.secret:
                signature = hmac.new(
                    config.secret.encode(),
                    body.encode(),
                    hashlib.sha256,
                ).hexdigest()
                headers["X-InsurBridge-Signature"] = signature

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(config.url, content=body, headers=headers)
                logger.info(
                    f"Webhook dispatched: {event_type} -> {config.url} | Status: {response.status_code}"
                )
        except Exception as e:
            logger.error(f"Webhook failed: {event_type} -> {config.url} | Error: {e}")


async def generate_batch_csv(tenant_id: str, policies: list, output_dir: str = "generated_docs") -> str:
    """
    Generate a nightly batch CSV for insurers without API capabilities.
    Legacy fallback for the Regulatory Handshake.
    """
    import csv
    from datetime import datetime
    import os

    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/batch_{tenant_id}_{datetime.now().strftime('%Y%m%d')}.csv"

    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            "policy_number", "holder_name", "holder_email", "product_type",
            "coverage_blocks", "premium_monthly", "premium_annual",
            "status", "bound_at",
        ])
        writer.writeheader()
        for policy in policies:
            writer.writerow({
                "policy_number": policy.policy_number,
                "holder_name": policy.holder_name,
                "holder_email": policy.holder_email,
                "product_type": policy.product_type,
                "coverage_blocks": policy.coverage_blocks,
                "premium_monthly": policy.premium_monthly,
                "premium_annual": policy.premium_annual,
                "status": policy.status,
                "bound_at": str(policy.bound_at),
            })

    logger.info(f"Batch CSV generated: {filename} with {len(policies)} policies")
    return filename
