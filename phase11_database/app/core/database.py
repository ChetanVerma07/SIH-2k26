"""
SQLAlchemy engine / session management.

This module is the single place that knows how to talk to PostgreSQL.
Everything above it (repositories, and later the FastAPI service layer)
should depend only on `get_session` / `SessionLocal`, never construct
engines themselves.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Shared declarative base for every ORM model in the project."""
    pass


def build_engine(database_url: str | None = None):
    settings = get_settings()
    url = database_url or settings.DATABASE_URL
    return create_engine(
        url,
        echo=settings.SQL_ECHO,
        pool_pre_ping=True,
        future=True,
    )


# Default engine/session factory used by the application at import time.
engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context-managed session with commit/rollback handled centrally so
    repositories never leak connections.

    Usage:
        with get_session() as session:
            repo = ProjectRepository(session)
            repo.create(...)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
