from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.core import Payment, Policy
from app.services.sla import record_policy_sla_event
import logging

logger = logging.getLogger(__name__)

# Commission rates (configurable per insurer in production)
DEFAULT_PARTNER_COMMISSION_RATE = 0.15  # 15%
DEFAULT_PLATFORM_FEE_RATE = 0.05  # 5%


async def process_payment(
    policy_number: str,
    amount: float,
    currency: str,
    gateway: str,
    db: AsyncSession,
) -> Payment:
    """
    Process a premium payment with automatic commission splitting.
    
    Split Logic:
    - Partner Commission: 15% (configurable)
    - Platform Fee: 5%
    - Insurer Net: 80%
    """
    # Find the policy
    result = await db.execute(select(Policy).where(Policy.policy_number == policy_number))
    policy = result.scalars().first()
    if not policy:
        raise ValueError(f"Policy {policy_number} not found")

    # Calculate splits
    partner_commission = amount * DEFAULT_PARTNER_COMMISSION_RATE if policy.partner_id else 0.0
    platform_fee = amount * DEFAULT_PLATFORM_FEE_RATE
    insurer_share = amount - partner_commission - platform_fee

    # In production: call Paystack/Stripe API here
    # For hackathon, we simulate the payment
    gateway_reference = f"sim_{gateway}_{policy_number}"

    payment = Payment(
        policy_id=policy.id,
        amount=amount,
        currency=currency,
        insurer_share=round(insurer_share, 2),
        partner_commission=round(partner_commission, 2),
        platform_fee=round(platform_fee, 2),
        gateway=gateway,
        gateway_reference=gateway_reference,
        status="success",  # Simulated for hackathon
    )

    db.add(payment)
    policy.status = "active"
    await db.commit()
    await db.refresh(payment)
    await db.refresh(policy)

    try:
        await record_policy_sla_event(db=db, policy=policy, event_type="policy_activated")
    except Exception as error:
        logger.warning(f"SLA policy_activated metric update skipped: {error}")

    logger.info(
        f"Payment processed: {amount} {currency} for {policy_number} | "
        f"Insurer: {insurer_share} | Partner: {partner_commission} | Platform: {platform_fee}"
    )

    return payment
