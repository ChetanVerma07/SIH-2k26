"""
Pytest fixtures for the database layer.

Tests run against a real PostgreSQL database (TEST_DATABASE_URL, or
DATABASE_URL + "_test" as a fallback -- see app.core.config). Schema is
created once per test session directly from the SQLAlchemy metadata
(Base.metadata.create_all) so tests don't depend on Alembic revisions
being up to date, and each test runs inside a transaction that is
rolled back afterwards so tests never leak state into each other.

If no PostgreSQL test server is reachable, the whole session is
skipped with a clear message -- this keeps the *production*
configuration strictly PostgreSQL while still letting the suite fail
gracefully in environments without a database.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models import Base


@pytest.fixture(scope="session")
def test_engine():
    settings = get_settings()
    url = settings.resolved_test_database_url()
    engine = create_engine(url, future=True)

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"PostgreSQL test database not reachable at {url!r}: {exc}")

    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def db_session(test_engine) -> Session:
    connection = test_engine.connect()
    transaction = connection.begin()
    SessionFactory = sessionmaker(bind=connection, future=True)
    session = SessionFactory()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
