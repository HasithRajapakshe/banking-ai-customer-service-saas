from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Tool Gateway"
    app_env: str = "development"

    app_host: str = "0.0.0.0"
    app_port: int = 8003

    banking_adapter_base_url: str = "http://127.0.0.1:8002"
    banking_adapter_api_key: str = "banking-adapter-dev-secret"

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