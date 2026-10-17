import logging
from contextlib import asynccontextmanager

# Configure logging before importing the app: the model gateway is built at
# import time and logs which provider is active.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

from app.core.pii import install_pii_masking  # noqa: E402

install_pii_masking()

from fastapi import FastAPI  # noqa: E402

from app.api.routes import chat_router  # noqa: E402
from app.clients.tool_gateway_client import tool_gateway_client  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.middleware import CorrelationIdMiddleware  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    install_pii_masking()  # uvicorn configures its handlers after import
    await tool_gateway_client.start()
    yield
    await tool_gateway_client.close()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="LangGraph AI orchestration service for Banking AI Customer Service SaaS",
    lifespan=lifespan,
)
app.add_middleware(CorrelationIdMiddleware)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ai-agent",
        "environment": settings.app_env,
        "model_provider": settings.model_provider,
    }


app.include_router(chat_router)
