import asyncio
import sys
sys.path.append("/app")
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.core import User

async def list_users():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        print(f"Total Users Found: {len(users)}")
        for u in users:
            print(f" - {u.email} ({u.role})")

if __name__ == "__main__":
    asyncio.run(list_users())
