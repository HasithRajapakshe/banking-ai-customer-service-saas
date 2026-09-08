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


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Synthetic Banking API for the Banking AI Customer Service SaaS",
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "synthetic-bank",
        "environment": settings.app_env,
    }


app.include_router(customers_router)
app.include_router(accounts_router)
app.include_router(cards_router)
app.include_router(payments_router)
app.include_router(beneficiaries_router)
app.include_router(loans_router)
app.include_router(complaints_router)