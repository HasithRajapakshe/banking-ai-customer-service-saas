import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import search, documents
from app.core.config import settings

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="RAG Service for Banking Knowledge",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(documents.router)

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "service": settings.app_name}
