"""
Test 1: database connection.
"""
from sqlalchemy import text


def test_connection_works(test_engine):
    with test_engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1
