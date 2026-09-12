from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from urllib.parse import urlsplit
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
    personal_api_token_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    auth_mode: Literal["personal_token", "better_auth"] = "personal_token"
    better_auth_url: str | None = None
    owner_user_id: str | None = None
    cors_origins: str = DEFAULT_CORS_ORIGINS
    log_level: str = "INFO"
    port: int = Field(default=8000, ge=1, le=65535)

    @field_validator("database_url", "database_direct_url")
    @classmethod
    def validate_postgres_url(cls, value: str) -> str:
        if not value.startswith(("postgresql://", "postgresql+psycopg://")):
            raise ValueError("must be a PostgreSQL URL")
        return value.replace("postgresql://", "postgresql+psycopg://", 1)

    @model_validator(mode="after")
    def validate_auth(self):
        if self.auth_mode == "personal_token" and not self.personal_api_token_sha256:
            raise ValueError("Personal token mode requires a token digest")
        if self.auth_mode == "better_auth":
            if not self.better_auth_url or not self.owner_user_id:
                raise ValueError("Better Auth requires its service URL and the owner's user ID")
            parsed = urlsplit(self.better_auth_url)
            if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError("Invalid Better Auth URL")
            if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}):
                raise ValueError("Better Auth requires HTTPS except on loopback")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


class CorsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cors_origins: str = DEFAULT_CORS_ORIGINS


@lru_cache
def get_cors_origins() -> str:
    return CorsSettings().cors_origins
