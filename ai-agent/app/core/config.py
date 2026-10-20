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

    # Model gateway. MODEL_PROVIDER: deterministic (keyword router, no LLM),
    # fake (scripted, tests only), ollama, gemini, openai or anthropic.
    model_provider: str = "deterministic"
    model_name: str = "deterministic-v1"
    ollama_base_url: str = "http://host.docker.internal:11434"
    # Ollama's default 4096-token window is smaller than the routing prompt
    # (all tool schemas) and Ollama truncates silently, so raise it.
    ollama_num_ctx: int = 8192
    google_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 1
    llm_temperature: float = 0.0
    tool_catalogue_ttl_seconds: float = 300.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
