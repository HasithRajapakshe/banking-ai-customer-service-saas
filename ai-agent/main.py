from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import chat_router
from app.clients.tool_gateway_client import tool_gateway_client
from app.core.config import settings
from app.core.middleware import CorrelationIdMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
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
