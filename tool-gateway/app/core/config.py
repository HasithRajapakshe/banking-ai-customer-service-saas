from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Tool Gateway"
    app_env: str = "development"

    app_host: str = "0.0.0.0"
    app_port: int = 8003

    banking_adapter_base_url: str = "http://127.0.0.1:8002"
    banking_adapter_api_key: str = "banking-adapter-dev-secret"

    redis_url: str = "redis://localhost:6379/2"

    # Audit persistence and role -> permission lookups. Unset in unit tests;
    # in a running stack every execution is written to tool_execution/audit_log.
    database_url: str | None = None
    permission_cache_ttl_seconds: float = 60.0

    # Internal identity token signed by the API Gateway (not the user JWT).
    internal_jwt_secret: str = "change-this-internal-service-secret"
    internal_jwt_issuer: str = "api-gateway"
    internal_jwt_audience: str = "internal-services"
    internal_jwt_leeway_seconds: int = 5

    request_timeout_seconds: float = 10.0

    max_connections: int = 20
    max_keepalive_connections: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()