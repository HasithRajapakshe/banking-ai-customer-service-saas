import logging
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth, chat, accounts
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api_gateway")

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Main entrypoint for frontend applications. Handles auth and routes requests.",
)

# CORS middleware
origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next: Callable) -> Response:
    from app.core.rate_limit import check_rate_limit
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    
    try:
        await check_rate_limit(request)
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    except Exception as exc:
        logger.exception("Unhandled error in API Gateway", extra={"correlation_id": correlation_id})
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred.",
                },
                "correlation_id": correlation_id,
            },
            headers={"X-Correlation-ID": correlation_id},
        )

# Include routers
from app.api.routes import auth, chat, accounts, admin
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(accounts.router)
app.include_router(admin.router)

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "service": settings.app_name}
