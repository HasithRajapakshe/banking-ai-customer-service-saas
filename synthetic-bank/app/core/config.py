import uuid

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Synthetic Banking API"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8001

    database_url: str

    internal_api_key: str

    bank_code: str
    tenant_id: uuid.UUID

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()