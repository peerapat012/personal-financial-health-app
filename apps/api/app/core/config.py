from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:1420,http://127.0.0.1:1420,"
    "tauri://localhost,http://tauri.localhost"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str
    database_direct_url: str
    personal_api_token_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    cors_origins: str = DEFAULT_CORS_ORIGINS
    log_level: str = "INFO"
    port: int = Field(default=8000, ge=1, le=65535)

    @field_validator("database_url", "database_direct_url")
    @classmethod
    def validate_postgres_url(cls, value: str) -> str:
        if not value.startswith(("postgresql://", "postgresql+psycopg://")):
            raise ValueError("must be a PostgreSQL URL")
        return value.replace("postgresql://", "postgresql+psycopg://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


class CorsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cors_origins: str = DEFAULT_CORS_ORIGINS


@lru_cache
def get_cors_origins() -> str:
    return CorsSettings().cors_origins
