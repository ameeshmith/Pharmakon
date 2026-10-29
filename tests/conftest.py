"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest

# Use an isolated SQLite database for tests
os.environ["DATABASE_URL"] = "sqlite:///./test_pharmakon.db"
os.environ["OPENFDA_API_KEY"] = "test_secret_openfda_key_999999"

from server.config import get_settings  # noqa: E402
from server.db import Base, get_engine, init_db  # noqa: E402
from server.http_client import http_client  # noqa: E402
from server.rate_limit import rate_limiter  # noqa: E402


@pytest.fixture(autouse=True)
def reset_state() -> Generator[None, None, None]:
    """Reset database tables, HTTP cache, and rate limiter before each test."""
    get_settings.cache_clear()
    engine = get_engine("sqlite:///./test_pharmakon.db")
    Base.metadata.drop_all(bind=engine)
    init_db("sqlite:///./test_pharmakon.db")
    http_client.clear_cache()
    rate_limiter.reset()
    yield
    http_client.clear_cache()
    rate_limiter.reset()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Clean up temporary test SQLite file after test suite finishes."""
    try:
        engine = get_engine()
        engine.dispose()
        for db_name in ("test_pharmakon.db", "test_medsafe.db"):
            db_file = Path(db_name)
            if db_file.exists():
                db_file.unlink()
    except Exception:
        pass
