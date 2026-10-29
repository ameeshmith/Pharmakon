"""Configuration and environment settings for Pharmakon MCP Server."""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

MEDICAL_DISCLAIMER = (
    "Informational only — not medical advice. Adverse event reports (FAERS) are "
    "unvalidated voluntary submissions and do not establish causation. Clinical "
    "decisions must be made by qualified healthcare professionals."
)


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Pharmakon — Drug Safety & Clinical Trials MCP"
    app_version: str = "0.1.0"

    # openFDA API Key (optional, raises limit from 1,000/day to 120,000/day)
    openfda_api_key: str = Field(default="", validation_alias="OPENFDA_API_KEY")

    # Optional NCBI E-utilities polite credentials
    ncbi_api_key: str = Field(default="", validation_alias="NCBI_API_KEY")
    ncbi_email: str = Field(
        default="opensource@pharmakon.dev", validation_alias="NCBI_EMAIL"
    )

    # Database URL (SQLite by default, swappable for PostgreSQL)
    database_url: str = Field(
        default="sqlite:///./pharmakon.db", validation_alias="DATABASE_URL"
    )

    # JWT Session config
    jwt_secret_key: str = Field(
        default="dev-secret-change-in-production-pharmakon-2026-key-32b",
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = Field(default=1440, validation_alias="JWT_EXPIRE_MINUTES")

    # Rate limits per API key
    rate_limit_per_minute: int = Field(
        default=30, validation_alias="RATE_LIMIT_PER_MINUTE"
    )
    rate_limit_per_day: int = Field(default=1000, validation_alias="RATE_LIMIT_PER_DAY")

    # Upstream response cache TTL
    cache_ttl_seconds: int = Field(default=3600, validation_alias="CACHE_TTL_SECONDS")

    # Network & CORS
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000",
        validation_alias="CORS_ORIGINS",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def effective_openfda_key(self) -> str:
        return (os.environ.get("OPENFDA_API_KEY") or self.openfda_api_key or "").strip()


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
