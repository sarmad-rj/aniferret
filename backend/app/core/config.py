import secrets
from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_DATABASE_URL = "sqlite+aiosqlite:///./aniferret.db"
_DEFAULT_CHROMA_PERSIST_DIR = "./chroma_store"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AniFerret"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"

    data_dir: str = Field(
        default=".",
        description="Base directory for persistent state (SQLite DB + ChromaDB store). "
        "Set to a mounted volume path (e.g. /app/data) in production — database_url and "
        "chroma_persist_dir are derived from it unless set explicitly, so one volume "
        "mount covers both. Local dev is untouched: the default '.' keeps today's "
        "relative-path behavior.",
    )
    database_url: str = _DEFAULT_DATABASE_URL
    gemini_api_key: str = ""
    chroma_persist_dir: str = _DEFAULT_CHROMA_PERSIST_DIR

    cors_origins: list[str] = ["http://localhost:5173"]

    jwt_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    """No hardcoded default — an empty or shared placeholder secret would let anyone
    forge tokens. Generates a random per-process secret when unset, so tokens simply
    don't survive a restart in dev unless JWT_SECRET_KEY is set explicitly in .env;
    fails closed rather than being silently insecure."""
    jwt_expire_minutes: int = 60 * 24 * 7

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    emails_from: str = ""
    """All left blank by default — matches gemini_api_key's pattern: email_service
    checks for a configured host before attempting to send, so a dev environment
    with no SMTP credentials degrades to a silent no-op (logged, not crashed)
    instead of failing registration/reset requests."""
    frontend_url: str = "http://localhost:5173"

    admin_email: str = ""
    admin_password: str = ""
    """Blank by default, same degrade-gracefully pattern as smtp_*/gemini_api_key —
    seed_admin_user() skips creating the admin account (logs a warning) rather than
    hardcoding real credentials in source, which would otherwise ship to version
    control in plaintext."""

    @model_validator(mode="after")
    def _derive_paths_from_data_dir(self) -> "Settings":
        """If DATA_DIR is set to something other than the default, point database_url
        and chroma_persist_dir inside it — unless they were explicitly overridden
        themselves, which always wins. Lets a single DATA_DIR volume mount (e.g. in
        the container) cover both the SQLite file and the ChromaDB store without
        requiring all three env vars to be set in lockstep."""
        if self.data_dir != ".":
            if self.database_url == _DEFAULT_DATABASE_URL:
                self.database_url = f"sqlite+aiosqlite:///{self.data_dir}/aniferret.db"
            if self.chroma_persist_dir == _DEFAULT_CHROMA_PERSIST_DIR:
                self.chroma_persist_dir = f"{self.data_dir}/chroma_store"
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
