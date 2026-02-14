import asyncio
import os
import sys
from datetime import datetime

# Add /app to sys.path to ensure we can import app modules
sys.path.append("/app")

from app.db.session import AsyncSessionLocal
from app.models.manual import UnderwritingManual
from app.core.security import encrypt_data
from app.services.ingestion import process_manual_ingestion
from sqlalchemy import select, delete

MANUALS_DIR = "/app/app/manuals"
UPLOAD_DIR = "/app/uploaded_manuals"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

async def seed_manuals():
    async with AsyncSessionLocal() as db:
        # Clear existing manuals
        print("Clearing existing manuals...")
        await db.execute(select(UnderwritingManual)) # Just to ensure import
        from sqlalchemy import delete
        await db.execute(delete(UnderwritingManual))
        await db.commit()
        
        manuals_to_seed = [
            ("heirs_general_auto.txt", "auto"),
            ("heirs_life_term.txt", "life"),
            ("heirs_gadget_device.txt", "gadget"),
        ]

        for filename, product_type in manuals_to_seed:
            file_path = os.path.join(MANUALS_DIR, filename)
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                continue

            print(f"Processing {filename}...")

            # 1. Read & Encrypt
            with open(file_path, "rb") as f:
                content = f.read()
            
            encrypted_content = encrypt_data(content)
            
            # 2. Save Encrypted File
            enc_filename = f"{product_type}_v1_{int(datetime.now().timestamp())}.enc"
            enc_path = os.path.join(UPLOAD_DIR, enc_filename)
            
            with open(enc_path, "wb") as f:
                f.write(encrypted_content)
            
            # 3. Create DB Record
            manual = UnderwritingManual(
                filename=filename,
                product_type=product_type,
                version="v1",
                encrypted_file_path=enc_path,
                is_active=True
            )
            db.add(manual)
            await db.commit()
            await db.refresh(manual)
            
            print(f"Created DB record for {filename} (ID: {manual.id})")

            # 4. Trigger Ingestion (LLM)
            print(f"Triggering LLM ingestion for {filename}...")
            await process_manual_ingestion(manual.id, db)
            print(f"Ingestion complete for {filename}")

if __name__ == "__main__":
    print("Starting Direct Manual Seeding...")
    asyncio.run(seed_manuals())
    print("Seeding Finished.")
