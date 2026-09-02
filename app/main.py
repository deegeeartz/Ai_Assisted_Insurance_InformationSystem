from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.config import settings
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Startup/Shutdown Lifespan: Create Tables & Seed Data ---
from app.db.base import Base
from app.db.session import engine, AsyncSessionLocal
from app.models import core, manual  # Import all models so they register with Base
from app.models.audit import AuditLog, UnderwritingDecisionLog
from app.models.chat_log import ChatLog
from app.db.init_db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.AUTO_CREATE_TABLES:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    if settings.AUTO_SEED_DATA:
        async with AsyncSessionLocal() as db:
            await init_db(db)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="InsurBridge AI - Liquid Logic Insurance Infrastructure",
    version="0.1.0",
    lifespan=lifespan,
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url, exc_info=exc)
    content = {"detail": "Internal server error"}
    if settings.EXPOSE_ERROR_DETAILS:
        content["error"] = str(exc)
    response = JSONResponse(status_code=500, content=content)
    origin = request.headers.get("origin")
    if origin and origin in origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

from fastapi.middleware.cors import CORSMiddleware

# Localhost dev origins are only allowed outside production. Production origins
# come from CORS_ORIGINS env var (comma-separated, e.g.
# "https://app.insurbridge.ai,https://portal.insurbridge.ai").
_IS_DEV = settings.ENVIRONMENT.lower() in ("development", "dev", "local")
_LOCALHOST_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:5173",
]
_extra = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
origins = list(dict.fromkeys((_LOCALHOST_ORIGINS if _IS_DEV else []) + _extra))  # deduplicate, preserve order

if not origins:
    logger.warning(
        "No CORS origins configured (ENVIRONMENT=%s, CORS_ORIGINS empty). "
        "Browser frontends will be blocked until CORS_ORIGINS is set.",
        settings.ENVIRONMENT,
    )

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
from app.api.endpoints import manuals, underwrite, auth, operations, partners, compliance, config, admin

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(manuals.router, prefix=f"{settings.API_V1_STR}/manuals", tags=["Manuals"])
app.include_router(config.router, prefix=f"{settings.API_V1_STR}/config", tags=["Configuration"])
app.include_router(underwrite.router, prefix=f"{settings.API_V1_STR}", tags=["Underwriting"])
app.include_router(operations.router, prefix=f"{settings.API_V1_STR}", tags=["operations"])
app.include_router(partners.router, prefix=f"{settings.API_V1_STR}/partners", tags=["partners"])
app.include_router(compliance.router, prefix=f"{settings.API_V1_STR}/compliance", tags=["compliance"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])

