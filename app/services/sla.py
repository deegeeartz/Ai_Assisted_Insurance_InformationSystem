from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.core import SLARecord
from app.models.manual import UnderwritingManual
from app.core.llm import get_llm
from langchain_core.messages import HumanMessage
import json
import logging

logger = logging.getLogger(__name__)


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
