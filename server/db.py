"""SQLAlchemy database engine and session management (SQLite & PostgreSQL ready)."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from server.config import get_settings


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy ORM models."""


_engine = None
_SessionLocal = None


def get_engine(database_url: str | None = None) -> Any:
    """Create or retrieve the SQLAlchemy engine."""
    global _engine, _SessionLocal
    url = database_url or get_settings().database_url
    if _engine is None or str(_engine.url) != url:
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return the configured sessionmaker."""
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


def init_db(database_url: str | None = None) -> None:
    """Initialize all database tables."""
    import server.models  # noqa: F401

    engine = get_engine(database_url)
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
