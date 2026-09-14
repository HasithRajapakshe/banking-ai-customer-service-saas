import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import CorrelationIdMiddleware
from app.factory import get_banking_provider


setup_logging()

logger = logging.getLogger(__name__)


# =========================
# Lifespan
# =========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    provider = get_banking_provider()
    await provider.start()

    logger.info(
        "Banking Adapter started "
        "(env=%s, provider=%s)",
        settings.app_env,
        settings.banking_provider,
    )

    yield

    await provider.close()

    logger.info("Banking Adapter stopped")


# =========================
# Application
# =========================

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Banking Adapter Service for the "
        "Banking AI Customer Service Platform"
    ),
    lifespan=lifespan,
)

app.add_middleware(CorrelationIdMiddleware)


# =========================
# Health Check
# =========================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "banking-adapter",
        "environment": settings.app_env,
        "provider": settings.banking_provider,
    }


# =========================
# Development Routes
# =========================

if settings.app_env == "development":
    from app.api.routes.dev import dev_router

    app.include_router(dev_router)