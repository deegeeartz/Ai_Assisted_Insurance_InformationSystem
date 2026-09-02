from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.core import User
from app.schemas.core import UserCreate, UserResponse, Token, LoginRequest
from app.services.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    generate_api_key,
    get_current_user,
)

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Restrict self-registration to safe roles only.
    # Privileged roles (insurer, admin, compliance_officer) must be created
    # by a superadmin or seeded at startup.
    ALLOWED_SELF_REGISTER_ROLES = {"consumer", "partner"}
    if user_data.role not in ALLOWED_SELF_REGISTER_ROLES:
        raise HTTPException(
            status_code=403,
            detail=f"Self-registration is not allowed for role '{user_data.role}'. Contact an administrator.",
        )

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    db_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        company_name=user_data.company_name,
        role=user_data.role,
    )

    # Generate API key for partners and insurers
    if user_data.role in ("partner", "insurer"):
        db_user.api_key = generate_api_key()

    # Set tenant_id for insurers (they are their own tenant)
    if user_data.role == "insurer":
        db_user.tenant_id = user_data.email  # Use email as tenant_id for simplicity

    db.add(db_user)
    
    from app.models.audit import AuditLog
    db.add(AuditLog(
        user_email=db_user.email,
        action="register",
        resource_type="user",
        resource_id=db_user.email,
        details=f"role: {db_user.role}",
    ))

    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    email = login_data.email.lower()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if user:
        is_valid = verify_password(login_data.password, user.hashed_password)

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    from app.models.audit import AuditLog
    db.add(AuditLog(
        user_id=user.id,
        user_email=user.email,
        action="login",
        resource_type="user",
        resource_id=user.email,
    ))
    await db.commit()

    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return Token(access_token=access_token, role=user.role)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
