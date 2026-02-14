from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.manual import UnderwritingManual
from app.schemas.manual import ManualResponse
from app.core.security import encrypt_data
import os
import aiofiles
from datetime import datetime

router = APIRouter()

UPLOAD_DIR = "uploaded_manuals"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


# Background task wrapper
async def run_ingestion_task(manual_id: int):
    from app.db.session import AsyncSessionLocal
    from app.services.ingestion import process_manual_ingestion

    async with AsyncSessionLocal() as session:
        await process_manual_ingestion(manual_id, session)


@router.post("/upload", response_model=ManualResponse)
async def upload_manual(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    product_type: str = Form(...),
    version: str = Form("v1"),
    db: AsyncSession = Depends(get_db),
):
    if not (file.filename.endswith(".pdf") or file.filename.endswith(".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are allowed.")

    content = await file.read()
    encrypted_content = encrypt_data(content)

    # Save encrypted file
    filename = f"{product_type}_{version}_{int(datetime.now().timestamp())}.enc"
    file_path = os.path.join(UPLOAD_DIR, filename)

    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(encrypted_content)

    # Create DB record
    db_manual = UnderwritingManual(
        filename=file.filename,
        product_type=product_type,
        version=version,
        encrypted_file_path=file_path,
        is_active=True,
    )
    db.add(db_manual)
    await db.commit()
    await db.refresh(db_manual)

    # Trigger Background Ingestion (Liquid Logic compilation)
    background_tasks.add_task(run_ingestion_task, db_manual.id)

    return db_manual


@router.get("/", response_model=list[ManualResponse])
async def list_manuals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UnderwritingManual))
    return result.scalars().all()
