from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.core import User
from app.services.auth import get_password_hash, generate_api_key
import logging
import os
import secrets

logger = logging.getLogger(__name__)

async def init_db(db: AsyncSession):
    """Seed the database with initial organization users.

    Demo passwords are never hardcoded: they come from SEED_DEMO_PASSWORD,
    or a random password is generated for this seed run and logged once.
    """

    demo_password = os.environ.get("SEED_DEMO_PASSWORD") or secrets.token_urlsafe(12)
    source = "SEED_DEMO_PASSWORD" if os.environ.get("SEED_DEMO_PASSWORD") else "generated for this seed run"
    logger.warning(
        "Demo seed password (%s): %r — shared by all seeded demo users. Change it before any real use.",
        source,
        demo_password,
    )

    orgs = [
        {
            "email": "admin@heirs-general.com",
            "full_name": "Admin - Heirs General",
            "company_name": "Heirs General Insurance",
            "role": "insurer", # Using insurer role for org admins
        },
        {
            "email": "admin@heirs-life.com",
            "full_name": "Admin - Heirs Life",
            "company_name": "Heirs Life Assurance",
            "role": "insurer",
        },
        {
            "email": "admin@heirs-gadget.com",
            "full_name": "Admin - Heirs Gadget",
            "company_name": "Heirs Gadget Insurance",
            "role": "insurer",
        },
        {
            "email": "partner@example.com",
            "full_name": "Demo Partner",
            "company_name": "TechResell Ltd",
            "role": "partner",
        },
        {
            "email": "compliance@example.com",
            "full_name": "Chief Compliance Officer",
            "company_name": "Heirs Holdings",
            "role": "compliance_officer",
        },
        {
            "email": "superadmin@heirsholdings.com",
            "full_name": "Platform Superadmin",
            "company_name": "Heirs Insurance Group",
            "role": "admin",
        }
    ]

    for org in orgs:
        result = await db.execute(select(User).where(User.email == org["email"]))
        user = result.scalars().first()

        if not user:
            logger.info(f"Seeding user: {org['email']}")
            new_user = User(
                email=org["email"],
                hashed_password=get_password_hash(demo_password),
                full_name=org["full_name"],
                company_name=org["company_name"],
                role=org["role"],
                tenant_id=org["email"] if org["role"] == "insurer" else None,
                api_key=generate_api_key() if org["role"] in ["insurer", "partner"] else None
            )
            db.add(new_user)
            
    # Seed platform configs
    from app.models.core import PlatformConfig
    configs = [
        {"key": "kill_switch", "value": "false", "description": "Global emergency API toggle"},
        {"key": "global_commission_rate", "value": "0.10", "description": "Default partner revenue share (10%)"}
    ]
    for conf in configs:
        res = await db.execute(select(PlatformConfig).where(PlatformConfig.key == conf["key"]))
        if not res.scalars().first():
            db.add(PlatformConfig(**conf))

    await db.commit()
