from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Banking Adapter"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8002

    banking_provider: str = "synthetic"

    synthetic_bank_base_url: str
    synthetic_bank_api_key: str

    request_timeout_seconds: float = 10.0

    read_retry_attempts: int = 2
    read_retry_base_delay_seconds: float = 0.25

    max_connections: int = 20
    max_keepalive_connections: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
