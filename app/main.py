from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="InsurBridge AI - Liquid Logic Insurance Infrastructure",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {"message": "Welcome to InsurBridge AI API", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# --- Routers ---
from app.api.endpoints import manuals, underwrite, auth, operations, partners, compliance

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(manuals.router, prefix=f"{settings.API_V1_STR}/manuals", tags=["Manuals"])
app.include_router(underwrite.router, prefix=f"{settings.API_V1_STR}", tags=["Underwriting"])
app.include_router(underwrite.router, prefix="/api/v1/underwrite", tags=["underwrite"])
app.include_router(operations.router, prefix="/api/v1", tags=["operations"])
app.include_router(partners.router, prefix="/api/v1/partners", tags=["partners"])
app.include_router(compliance.router, prefix="/api/v1/compliance", tags=["compliance"])


# --- Startup: Create Tables ---
from app.db.base import Base
from app.db.session import engine
from app.models import core, manual  # Import all models so they register with Base


@app.on_event("startup")
async def startup_event():
    # Only create tables if NOT using Alembic (for Hackathon speed)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
