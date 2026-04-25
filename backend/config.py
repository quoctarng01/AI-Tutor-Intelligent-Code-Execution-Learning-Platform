from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Tutor API"
    api_prefix: str = "/api/v1"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_tutor"
    db_pool_size: int = 20
    db_max_overflow: int = 40
    db_pool_recycle: int = 3600

    # Security
    secret_key: str = "change-me-in-production-use-strong-random-key"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # CORS - comma-separated list of origins
    cors_origins: str = "http://localhost:5173,http://localhost:5174"

    # LLM / Groq
    openai_api_key: str = ""

    # Code Execution
    judge0_api_key: str = ""
    judge0_base_url: str = "https://judge0-ce.p.rapidapi.com"

    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_llm_per_minute: int = 10

    # Redis / Caching
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
