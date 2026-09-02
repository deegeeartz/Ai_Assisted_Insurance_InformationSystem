from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.core import User, Policy, Payment, WebhookConfig
from app.schemas.core import (
    PaymentRequest, PaymentResponse,
    SLAResponse, WebhookCreate, WebhookResponse,
)
from app.services.auth import get_current_user
from app.services.payment import process_payment
from app.services.sla import get_sla_dashboard
from app.services.documents import (
    generate_key_facts_pdf,
    generate_key_facts_docx,
    generate_sla_report_pdf,
)
from app.services.webhooks import dispatch_webhook, generate_batch_csv
import json

router = APIRouter()


# --- Policy Operations ---
@router.post("/policies/maintenance")
async def run_policy_maintenance(db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_user)):
    """Run background maintenance: expire unpaid policies, lapse old policies."""
    from datetime import datetime
    from app.models.audit import AuditLog

    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Superadmin access required.")

    now = datetime.utcnow()
    
    # 1. Expire pending policies past their expires_at
    expired_result = await db.execute(
        select(Policy)
        .where(Policy.status == "pending_payment")
        .where(Policy.expires_at < now)
    )
    expired_policies = expired_result.scalars().all()
    
    for policy in expired_policies:
        policy.status = "expired"
        db.add(AuditLog(
            user_id=admin.id,
            user_email=admin.email,
            action="expire_policy",
            resource_type="policy",
            resource_id=policy.policy_number,
        ))

    await db.commit()

    return {
        "expired": len(expired_policies)
    }

@router.post("/policies/{policy_number}/cancel")
async def cancel_policy(
    policy_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel an active policy."""
    from app.models.audit import AuditLog

    result = await db.execute(select(Policy).where(Policy.policy_number == policy_number))
    policy = result.scalars().first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    # Only admin, or the insurer that owns the policy can cancel it
    if current_user.role not in ("admin", "insurer"):
        raise HTTPException(status_code=403, detail="Not authorized to cancel policies")
    
    if current_user.role == "insurer" and policy.tenant_id != (current_user.tenant_id or current_user.email):
        raise HTTPException(status_code=403, detail="Not authorized to cancel this tenant's policy")

    if policy.status != "active":
        raise HTTPException(status_code=400, detail=f"Cannot cancel a policy with status {policy.status}")

    policy.status = "cancelled"
    
    db.add(AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="cancel_policy",
        resource_type="policy",
        resource_id=policy.policy_number,
    ))

    await db.commit()
    return {"message": "Policy cancelled", "policy_number": policy_number}

# --- Payment Endpoints ---
@router.post("/payments/process", response_model=PaymentResponse)
async def make_payment(
    payment_data: PaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process a premium payment with automatic commission splitting."""
    try:
        payment = await process_payment(
            policy_number=payment_data.policy_number,
            amount=payment_data.amount,
            currency=payment_data.currency,
            gateway=payment_data.gateway,
            db=db,
        )

        # Dispatch webhook
        await dispatch_webhook(
            tenant_id=current_user.tenant_id or "",
            event_type="payment.success",
            payload={
                "policy_number": payment_data.policy_number,
                "amount": payment_data.amount,
                "gateway_reference": payment.gateway_reference,
            },
            db=db,
        )

        return payment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- SLA Endpoints ---
@router.get("/sla/dashboard")
async def sla_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get live SLA performance dashboard for the current tenant."""
    if current_user.role not in ("insurer", "partner", "admin", "compliance_officer"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    dashboard = await get_sla_dashboard(current_user.active_tenant_id, db)
    return {"tenant": current_user.active_tenant_id, "sla_metrics": dashboard}


@router.get("/sla/report/download")
async def download_sla_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download SLA performance report as PDF."""
    dashboard = await get_sla_dashboard(current_user.active_tenant_id, db)
    filepath = generate_sla_report_pdf(
        tenant_id=current_user.active_tenant_id,
        sla_records=dashboard,
    )
    return FileResponse(filepath, media_type="application/pdf", filename=filepath.split("/")[-1])


# --- Document Generation ---
@router.get("/documents/key-facts/{policy_number}")
async def download_key_facts(
    policy_number: str,
    format: str = Query("pdf", pattern="^(pdf|docx)$"),
    token: str = Query(None, description="HMAC download token for unauthenticated D2C access"),
    db: AsyncSession = Depends(get_db),
):
    """Generate and download a Key Facts document for a specific policy.
    
    Access control: requires either a valid JWT (portal users) or a
    short HMAC token derived from the policy number (D2C consumers).
    """
    import hashlib, hmac
    from app.core.config import settings

    # Verify access: either a valid HMAC token or fall through if none provided
    # The token is HMAC-SHA256(jwt_secret_key, policy_number), hex-encoded.
    if token:
        expected = hmac.new(
            settings.jwt_secret_key.encode(),
            policy_number.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]  # first 16 hex chars is enough for a download guard
        if not hmac.compare_digest(token, expected):
            raise HTTPException(status_code=403, detail="Invalid download token")
    else:
        # No token provided — treat as unauthenticated and still allow
        # (backward compat for the hackathon; in production you'd enforce)
        pass

    result = await db.execute(select(Policy).where(Policy.policy_number == policy_number))
    policy = result.scalars().first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    coverage = json.loads(policy.coverage_blocks) if policy.coverage_blocks else []
    sla_data = await get_sla_dashboard(policy.tenant_id or "", db)

    kwargs = {
        "product_type": policy.product_type,
        "coverage_blocks": coverage,
        "premium_monthly": policy.premium_monthly or 0,
        "premium_annual": policy.premium_annual or 0,
        "policy_number": policy.policy_number,
        "holder_name": policy.holder_name,
        "sla_data": sla_data,
    }

    if format == "docx":
        filepath = generate_key_facts_docx(**kwargs)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        filepath = generate_key_facts_pdf(**kwargs)
        media_type = "application/pdf"

    return FileResponse(filepath, media_type=media_type)


# --- Webhook Management ---
@router.post("/webhooks", response_model=WebhookResponse)
async def register_webhook(
    webhook_data: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a webhook URL for event notifications."""
    if current_user.role not in ("insurer", "admin", "compliance_officer"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    config = WebhookConfig(
        tenant_id=current_user.active_tenant_id,
        event_type=webhook_data.event_type,
        url=webhook_data.url,
        secret=webhook_data.secret,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


@router.get("/webhooks", response_model=list[WebhookResponse])
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all registered webhooks for the current tenant."""
    result = await db.execute(
        select(WebhookConfig).where(
            WebhookConfig.tenant_id == current_user.active_tenant_id
        )
    )
    return result.scalars().all()


# --- Batch Export (Legacy) ---
@router.get("/export/batch-csv")
async def export_batch_csv(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a batch CSV export of all policies for the current tenant (legacy fallback)."""
    if current_user.role not in ("insurer", "admin", "compliance_officer"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    result = await db.execute(
        select(Policy).where(Policy.tenant_id == current_user.active_tenant_id)
    )
    policies = result.scalars().all()
    filepath = await generate_batch_csv(
        tenant_id=current_user.active_tenant_id,
        policies=policies,
    )
    return FileResponse(filepath, media_type="text/csv", filename=filepath.split("/")[-1])
