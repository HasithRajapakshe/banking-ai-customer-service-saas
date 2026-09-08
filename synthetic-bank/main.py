
from fastapi import FastAPI

from app.api.routes import (
    accounts_router,
    cards_router,
    customers_router,
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

