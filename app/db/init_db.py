from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.core import User
from app.services.auth import get_password_hash, generate_api_key
import logging

logger = logging.getLogger(__name__)

async def init_db(db: AsyncSession):
    """Seed the database with initial organization users."""
    
    orgs = [
        {
            "email": "admin@heirs-general.com",
            "full_name": "Admin - Heirs General",
            "company_name": "Heirs General Insurance",
            "role": "insurer", # Using insurer role for org admins
            "password": "password"
        },
        {
            "email": "admin@heirs-life.com",
            "full_name": "Admin - Heirs Life",
            "company_name": "Heirs Life Assurance",
            "role": "insurer",
            "password": "password"
        },
        {
            "email": "admin@heirs-gadget.com",
            "full_name": "Admin - Heirs Gadget",
            "company_name": "Heirs Gadget Insurance",
            "role": "insurer",
            "password": "password"
        },
        {
            "email": "partner@example.com",
            "full_name": "Demo Partner",
            "company_name": "TechResell Ltd",
            "role": "partner",
            "password": "password"
        },
        {
            "email": "compliance@example.com",
            "full_name": "Chief Compliance Officer",
            "company_name": "Heirs Holdings",
            "role": "compliance_officer",
            "password": "password"
        }
    ]

    for org in orgs:
        result = await db.execute(select(User).where(User.email == org["email"]))
        user = result.scalars().first()
        
        if not user:
            logger.info(f"Seeding user: {org['email']}")
            new_user = User(
                email=org["email"],
                hashed_password=get_password_hash(org["password"]),
                full_name=org["full_name"],
                company_name=org["company_name"],
                role=org["role"],
                tenant_id=org["email"] if org["role"] == "insurer" else None,
                api_key=generate_api_key() if org["role"] in ["insurer", "partner"] else None
            )
            db.add(new_user)
    
    await db.commit()
