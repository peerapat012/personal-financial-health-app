from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str
    database_direct_url: str
    personal_api_token_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
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
