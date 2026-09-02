import secrets
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AniFerret"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"

    database_url: str = "sqlite+aiosqlite:///./aniferret.db"

    gemini_api_key: str = ""
    chroma_persist_dir: str = "./chroma_store"

    cors_origins: list[str] = ["http://localhost:5173"]

    jwt_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    """No hardcoded default — an empty or shared placeholder secret would let anyone
    forge tokens. Generates a random per-process secret when unset, so tokens simply
    don't survive a restart in dev unless JWT_SECRET_KEY is set explicitly in .env;
    fails closed rather than being silently insecure."""
    jwt_expire_minutes: int = 60 * 24 * 7


@lru_cache
def get_settings() -> Settings:
    return Settings()
