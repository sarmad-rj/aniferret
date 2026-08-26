from functools import lru_cache

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
