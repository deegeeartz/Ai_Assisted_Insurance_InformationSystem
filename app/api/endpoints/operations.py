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
    if current_user.role not in ("insurer", "partner", "admin"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    dashboard = await get_sla_dashboard(current_user.tenant_id or current_user.email, db)
    return {"tenant": current_user.tenant_id or current_user.email, "sla_metrics": dashboard}


@router.get("/sla/report/download")
async def download_sla_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download SLA performance report as PDF."""
    dashboard = await get_sla_dashboard(current_user.tenant_id or current_user.email, db)
    filepath = generate_sla_report_pdf(
        tenant_id=current_user.tenant_id or current_user.email,
        sla_records=dashboard,
    )
    return FileResponse(filepath, media_type="application/pdf", filename=filepath.split("/")[-1])


# --- Document Generation ---
@router.get("/documents/key-facts/{policy_number}")
async def download_key_facts(
    policy_number: str,
    format: str = Query("pdf", regex="^(pdf|docx)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and download a Key Facts document for a specific policy."""
    result = await db.execute(select(Policy).where(Policy.policy_number == policy_number))
    policy = result.scalars().first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    coverage = json.loads(policy.coverage_blocks) if policy.coverage_blocks else []
    sla_data = await get_sla_dashboard(policy.tenant_id or "", db)

    if format == "docx":
        filepath = generate_key_facts_docx(
            product_type=policy.product_type,
            coverage_blocks=coverage,
            premium_monthly=policy.premium_monthly or 0,
            premium_annual=policy.premium_annual or 0,
            policy_number=policy.policy_number,
            holder_name=policy.holder_name,
            sla_data=sla_data,
        )
        return FileResponse(filepath, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        filepath = generate_key_facts_pdf(
            product_type=policy.product_type,
            coverage_blocks=coverage,
            premium_monthly=policy.premium_monthly or 0,
            premium_annual=policy.premium_annual or 0,
            policy_number=policy.policy_number,
            holder_name=policy.holder_name,
            sla_data=sla_data,
        )
        return FileResponse(filepath, media_type="application/pdf")


# --- Webhook Management ---
@router.post("/webhooks", response_model=WebhookResponse)
async def register_webhook(
    webhook_data: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a webhook URL for event notifications."""
    if current_user.role not in ("insurer", "admin"):
        raise HTTPException(status_code=403, detail="Only insurers can register webhooks")

    config = WebhookConfig(
        tenant_id=current_user.tenant_id or current_user.email,
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
            WebhookConfig.tenant_id == (current_user.tenant_id or current_user.email)
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
    if current_user.role not in ("insurer", "admin"):
        raise HTTPException(status_code=403, detail="Only insurers can export batch data")

    result = await db.execute(
        select(Policy).where(Policy.tenant_id == (current_user.tenant_id or current_user.email))
    )
    policies = result.scalars().all()
    filepath = await generate_batch_csv(
        tenant_id=current_user.tenant_id or current_user.email,
        policies=policies,
    )
    return FileResponse(filepath, media_type="text/csv", filename=filepath.split("/")[-1])
