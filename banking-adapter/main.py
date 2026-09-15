import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import (
    accounts_router,
    beneficiaries_router,
    cards_router,
    complaints_router,
    customers_router,
    loans_router,
    payments_router,
)
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import CorrelationIdMiddleware
from app.factory import get_banking_provider


setup_logging()

logger = logging.getLogger(__name__)


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


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "banking-adapter",
        "environment": settings.app_env,
        "provider": settings.banking_provider,
    }


# Production/internal API
app.include_router(customers_router)
app.include_router(accounts_router)
app.include_router(cards_router)
app.include_router(payments_router)
app.include_router(beneficiaries_router)
app.include_router(loans_router)
app.include_router(complaints_router)


# Development-only test endpoints
if settings.app_env == "development":
    from app.api.routes.dev import dev_router

    app.include_router(dev_router)