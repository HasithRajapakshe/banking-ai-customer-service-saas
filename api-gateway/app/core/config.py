from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "API Gateway"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8001

    # Database
    database_url: str = "postgresql+asyncpg://banking_app:change_me@localhost:5432/banking_ai"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret: str = "change-this-to-a-long-random-secret-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Internal service URLs
    ai_agent_base_url: str = "http://ai-agent:8004"
    tool_gateway_base_url: str = "http://tool-gateway:8003"
    synthetic_bank_base_url: str = "http://synthetic-bank:8000"

    # Internal API keys
    tool_gateway_api_key: str = "tool-gateway-internal-key-dev"
    synthetic_bank_api_key: str = "change-this-to-a-secure-internal-key-in-production"

    # Tenant config
    tenant_id: str = "f498100f-80c4-467e-84ec-ebfe5470b442"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
