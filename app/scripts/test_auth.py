import asyncio
import sys
sys.path.append("/app")
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.core import User
from app.services.auth import verify_password, get_password_hash

async def test_auth():
    email = "partner@example.com"
    password = "password"
    
    print(f"Testing auth for {email} with password '{password}'")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        if not user:
            print("User not found!")
            return

        print(f"User found: {user.email}")
        print(f"Stored Hash: {user.hashed_password[:10]}...")
        
        # Test Verification
        is_valid = verify_password(password, user.hashed_password)
        print(f"Verify Result: {is_valid}")
        
        # Test Hashing Consistency
        new_hash = get_password_hash(password)
        print(f"New Hash of 'password': {new_hash[:10]}...")
        is_valid_new = verify_password(password, new_hash)
        print(f"Verify New Hash: {is_valid_new}")

if __name__ == "__main__":
    asyncio.run(test_auth())
