from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

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
from app.core.errors import AppError
from app.core.exception_handlers import (
    app_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.middleware import CorrelationIdMiddleware
from app.core.security import require_internal_api_key
from app.core.tenant import require_configured_tenant


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Synthetic Banking API for the Banking AI Customer Service SaaS",
)


# =========================
# Middleware
# =========================

app.add_middleware(CorrelationIdMiddleware)


# =========================
# Exception Handlers
# =========================

app.add_exception_handler(
    AppError,
    app_error_handler,
)

app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    Exception,
    unhandled_exception_handler,
)


# =========================
# Health Check
# =========================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "synthetic-bank",
        "environment": settings.app_env,
        "bank_code": settings.bank_code,
    }


# =========================
# Internal API Security
# =========================

internal_dependencies = [
    Depends(require_internal_api_key),
    Depends(require_configured_tenant),
]


# =========================
# API Routers
# =========================

app.include_router(
    customers_router,
    dependencies=internal_dependencies,
)

app.include_router(
    accounts_router,
    dependencies=internal_dependencies,
)

app.include_router(
    cards_router,
    dependencies=internal_dependencies,
)

app.include_router(
    payments_router,
    dependencies=internal_dependencies,
)

app.include_router(
    beneficiaries_router,
    dependencies=internal_dependencies,
)

app.include_router(
    loans_router,
    dependencies=internal_dependencies,
)

app.include_router(
    complaints_router,
    dependencies=internal_dependencies,
)