from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.config import settings
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="InsurBridge AI - Liquid Logic Insurance Infrastructure",
    version="0.1.0",
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    logger.error(f"Unhandled error on {request.method} {request.url}:\n{''.join(tb)}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": ''.join(tb)},
    )

from fastapi.middleware.cors import CORSMiddleware

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Welcome to InsurBridge AI API", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# --- Routers ---
from app.api.endpoints import manuals, underwrite, auth, operations, partners, compliance, config

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(manuals.router, prefix=f"{settings.API_V1_STR}/manuals", tags=["Manuals"])
app.include_router(config.router, prefix=f"{settings.API_V1_STR}/config", tags=["Configuration"])
app.include_router(underwrite.router, prefix=f"{settings.API_V1_STR}", tags=["Underwriting"])
app.include_router(underwrite.router, prefix="/api/v1/underwrite", tags=["underwrite"])
app.include_router(operations.router, prefix="/api/v1", tags=["operations"])
app.include_router(partners.router, prefix="/api/v1/partners", tags=["partners"])
app.include_router(compliance.router, prefix="/api/v1/compliance", tags=["compliance"])


# --- Startup: Create Tables & Seed Data ---
from app.db.base import Base
from app.db.session import engine, AsyncSessionLocal
from app.models import core, manual  # Import all models so they register with Base
from app.models.chat_log import ChatLog
from app.db.init_db import init_db

@app.on_event("startup")
async def startup_event():
    # Only create tables if NOT using Alembic (for Hackathon speed)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed data
    async with AsyncSessionLocal() as db:
        await init_db(db)
