from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Agent Service"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8004

    tool_gateway_base_url: str = "http://127.0.0.1:8003"
    rag_base_url: str = "http://127.0.0.1:8005"
    request_timeout_seconds: float = 15.0
    max_agent_steps: int = 8
    max_tool_calls: int = 3

    model_provider: str = "deterministic"
    model_name: str = "deterministic-v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
