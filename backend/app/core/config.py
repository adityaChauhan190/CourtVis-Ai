"""
Court Vision AI — Application Configuration

Uses pydantic-settings for environment variable management.
All secrets must be injected via .env file or environment variables.
"""
from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────────
    APP_NAME: str = "Court Vision AI"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # ── API ────────────────────────────────────────────────────────────────────
    API_PREFIX: str = "/api"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # ── Database ───────────────────────────────────────────────────────────────
    # Supports both PostgreSQL (production/Docker) and SQLite (quick local dev)
    # Set to postgresql://... for full production use
    DATABASE_URL: str = "sqlite:///./court_vision.db"

    # ── Storage ────────────────────────────────────────────────────────────────
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    LOCAL_STORAGE_PATH: str = "./storage/documents"
    MAX_UPLOAD_SIZE_MB: int = 50

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # ── Auth ───────────────────────────────────────────────────────────────────
    # Phase 1: development mode uses a single auto-authenticated dev user.
    # Set AUTH_MODE=production and configure JWT for real authentication.
    AUTH_MODE: Literal["development", "production"] = "development"
    DEV_USER_ID: str = "00000000-0000-0000-0000-000000000001"
    DEV_USER_EMAIL: str = "counsel@courtvision.dev"
    DEV_USER_NAME: str = "Dev Counsel"

    JWT_SECRET_KEY: str = "REPLACE_WITH_SECURE_RANDOM_SECRET_KEY_MIN_32_CHARS"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── AI / Groq ──────────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_MAX_TOKENS: int = 2048
    MAX_CONTEXT_CHARS: int = 18000  # ~4.5k tokens; fits within Groq free-tier 8k TPM

    # ── Background Workers (Redis) ─────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Logging ────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
