import asyncio
import sys
sys.path.append("/app")
from app.db.session import AsyncSessionLocal
from app.models.manual import UnderwritingManual
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(UnderwritingManual))
        manuals = result.scalars().all()
        if not manuals:
            print("No manuals found in DB.")
        for m in manuals:
            print(f"ID: {m.id}, Filename: {m.filename}, HasRules: {bool(m.compiled_rules)}")
            if m.compiled_rules:
                print(f"Sample Rules: {m.compiled_rules[:100]}...")
            else:
                print("Rules empty!")

if __name__ == "__main__":
    asyncio.run(check())
