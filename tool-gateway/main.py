import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import tools_router
from app.clients.banking_adapter_client import (
    banking_adapter_client,
)
from app.core.config import settings
from app.core.middleware import CorrelationIdMiddleware
from app.tools.registry import register_default_tools

# Without this the root logger stays at WARNING and INFO audit events
# ("Tool executed", "Tool awaiting confirmation") are dropped.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await banking_adapter_client.start()

    register_default_tools()

    yield

    await banking_adapter_client.close()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Secure Tool Gateway for the "
        "Banking AI Customer Service SaaS"
    ),
    lifespan=lifespan,
)


app.add_middleware(
    CorrelationIdMiddleware
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "tool-gateway",
        "environment": settings.app_env,
    }


app.include_router(tools_router)