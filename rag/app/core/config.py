import uuid
from datetime import datetime

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RAG Service"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8005

    # Database
    database_url: str = "postgresql+asyncpg://banking_app:change_me_in_production@localhost:5432/banking_ai"

    # Embeddings
    embedding_provider: str = "mock"
    embedding_model: str = "text-embedding-3-small"
    openai_api_key: str | None = None

    # Chunking
    chunk_size: int = 1000
    chunk_overlap: int = 200

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
