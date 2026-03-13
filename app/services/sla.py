from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.core import SLARecord
from app.models.core import Policy
from app.models.manual import UnderwritingManual
from app.core.llm import get_llm
from langchain_core.messages import HumanMessage
import json
import logging
import re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _parse_duration_to_seconds(value: str) -> float | None:
    if not value:
        return None

    text = value.strip().lower()
    match = re.search(r"(\d+(?:\.\d+)?)\s*(second|seconds|sec|s|minute|minutes|min|m|hour|hours|hr|hrs|h|day|days|d)", text)
    if not match:
        return None

    amount = float(match.group(1))
    unit = match.group(2)

    if unit in {"second", "seconds", "sec", "s"}:
        return amount
    if unit in {"minute", "minutes", "min", "m"}:
        return amount * 60
    if unit in {"hour", "hours", "hr", "hrs", "h"}:
        return amount * 3600
    if unit in {"day", "days", "d"}:
        return amount * 86400

    return None


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{round(seconds, 2)} seconds"
    if seconds < 3600:
        return f"{round(seconds / 60, 2)} minutes"
    if seconds < 86400:
        return f"{round(seconds / 3600, 2)} hours"
    return f"{round(seconds / 86400, 2)} days"


def _metric_matches_event(metric_name: str, event_type: str) -> bool:
    metric = (metric_name or "").strip().lower()

    if event_type == "policy_created":
        keywords = ["quote", "response", "underwriting", "decision"]
        return any(word in metric for word in keywords)

    if event_type == "policy_activated":
        keywords = ["issuance", "issue", "activation", "payment", "bind"]
        return any(word in metric for word in keywords)

    return False


async def record_policy_sla_event(
    db: AsyncSession,
    policy: Policy,
    event_type: str,
) -> int:
    """
    Update SLA records for a policy lifecycle event.

    - `policy_created`: measures quote/underwriting response-time style SLAs
    - `policy_activated`: measures issuance/activation-time style SLAs
    """
    if not policy or not policy.tenant_id:
        return 0

    result = await db.execute(
        select(SLARecord).where(
            SLARecord.tenant_id == policy.tenant_id,
            SLARecord.product_type == policy.product_type,
        )
    )
    records = result.scalars().all()
    if not records:
        return 0

    now = datetime.now(timezone.utc)
    bound_at = policy.bound_at
    if bound_at and bound_at.tzinfo is None:
        bound_at = bound_at.replace(tzinfo=timezone.utc)

    elapsed_seconds = 0.0
    if bound_at:
        elapsed_seconds = max((now - bound_at).total_seconds(), 0.0)

    updated_count = 0
    for record in records:
        if not _metric_matches_event(record.metric_name, event_type):
            continue

        promised_seconds = _parse_duration_to_seconds(record.promised_value or "")
        if promised_seconds is None:
            continue

        record.actual_value = _format_duration(elapsed_seconds)
        record.is_breached = elapsed_seconds > promised_seconds
        record.measured_at = now
        updated_count += 1

    if updated_count:
        await db.commit()

    return updated_count


async def extract_slas_from_manual(manual_id: int, tenant_id: str, db: AsyncSession):
    """
    Extract SLA commitments from compiled rules and store them.
    Called after manual ingestion completes.
    """
    result = await db.execute(
        select(UnderwritingManual).where(UnderwritingManual.id == manual_id)
    )
    manual = result.scalars().first()
    if not manual or not manual.compiled_rules:
        return

    try:
        rules = json.loads(manual.compiled_rules)
        slas = rules.get("slas", {})

        for metric_name, promised_value in slas.items():
            sla_record = SLARecord(
                tenant_id=tenant_id,
                product_type=manual.product_type,
                metric_name=metric_name,
                promised_value=str(promised_value),
            )
            db.add(sla_record)

        await db.commit()
        logger.info(f"Extracted {len(slas)} SLA metrics for manual {manual_id}")
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Failed to extract SLAs: {e}")


async def get_sla_dashboard(tenant_id: str, db: AsyncSession) -> list[dict]:
    """Get all SLA metrics for a tenant with breach status."""
    result = await db.execute(
        select(SLARecord).where(SLARecord.tenant_id == tenant_id)
    )
    records = result.scalars().all()
    return [
        {
            "metric": r.metric_name,
            "promised": r.promised_value,
            "actual": r.actual_value or "Not yet measured",
            "breached": r.is_breached,
            "product": r.product_type,
        }
        for r in records
    ]
