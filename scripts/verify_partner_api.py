import asyncio
import os
import sys
import json
import urllib.request
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.models.core import User

async def get_test_partner_key():
    print(f"Connecting to DB: {settings.database_url}")
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == "partner@example.com"))
        user = result.scalars().first()
        if user:
            print(f"Found Partner: {user.email}")
            return user.api_key
        return None

def call_underwrite_api(api_key):
    url = "http://localhost:8000/api/v1/underwrite"
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key
    }
    payload = {
        "age": 35,
        "gender": "male",
        "occupation": "software engineer",
        "natural_language_query": "I want life insurance for my family",
        "holder_name": "API Verification User",
        "holder_email": "verify@partner.com"
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            print("\n✅ API Response Success:")
            print(f"Policy Number: {data.get('policy_number')}")
            print(f"Status: {data.get('status')}")
            print(f"Premium: {data.get('premium_monthly')}")
            return True
    except urllib.error.URLError as e:
        print(f"\n❌ API Request Failed: {e}")
        try:
            print(e.read().decode('utf-8'))
        except:
            pass
        return False

async def main():
    print("--- Verifying Partner API Integration ---")
    
    # 1. Get Key
    api_key = await get_test_partner_key()
    if not api_key:
        print("❌ Could not find partner@example.com in DB. Please run seed script first.")
        return

    print(f"API Key: {api_key[:10]}...")

    # 2. Call API
    success = call_underwrite_api(api_key)
    
    if success:
        print("\n🎉 Verification Complete! Partner API is working and binding policies.")
    else:
        print("\n⚠️ Verification Failed. Is the backend running on port 8000? (docker-compose up)")

if __name__ == "__main__":
    asyncio.run(main())
