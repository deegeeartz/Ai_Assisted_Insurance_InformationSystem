from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.manual import UnderwritingManual
from app.models.core import User
from app.schemas.manual import ManualResponse
from app.core.security import encrypt_data
from app.services.auth import get_current_user
from app.services.tenant import manual_tenant_from_product
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
    current_user: User = Depends(get_current_user),
):
    # Only insurers can upload underwriting manuals
    if current_user.role != "insurer":
        raise HTTPException(status_code=403, detail="Only insurer admins can upload underwriting manuals.")

    if not (file.filename.endswith(".pdf") or file.filename.endswith(".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are allowed.")

    content = await file.read()
    encrypted_content = encrypt_data(content)

    # Save encrypted file
    filename = f"{product_type}_{version}_{int(datetime.now().timestamp())}.enc"
    file_path = os.path.join(UPLOAD_DIR, filename)

    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(encrypted_content)

    # Prefer the uploading user's explicit tenant_id; fall back to product-type heuristic
    # so the field is always populated (never left NULL on new records).
    tenant_id = current_user.tenant_id or manual_tenant_from_product(product_type)

    # Create DB record
    db_manual = UnderwritingManual(
        filename=file.filename,
        product_type=product_type,
        version=version,
        encrypted_file_path=file_path,
        is_active=True,
        tenant_id=tenant_id,
    )
    db.add(db_manual)
    
    from app.models.audit import AuditLog
    db.add(AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="upload_manual",
        resource_type="manual",
        resource_id=file.filename,
        details=f"product: {product_type}, tenant: {tenant_id}",
    ))

    await db.commit()
    await db.refresh(db_manual)

    # Trigger Background Ingestion (Liquid Logic compilation)
    background_tasks.add_task(run_ingestion_task, db_manual.id)

    return db_manual


@router.get("/", response_model=list[ManualResponse])
async def list_manuals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(UnderwritingManual)
    # Tenant-scope for insurer and compliance roles; admin (superadmin) sees all
    if current_user.role in ("insurer", "compliance_officer"):
        query = query.where(UnderwritingManual.tenant_id == (current_user.tenant_id or current_user.email))
    
    result = await db.execute(query)
    return result.scalars().all()
