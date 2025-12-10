"""Database configuration and session management."""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Database URL from environment or default to PostgreSQL
# Use postgresql+psycopg for psycopg3 driver
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://mcpkart:mcpkart_dev@localhost:5432/mcpkart"
)

# SQLite-specific settings (for backwards compatibility)
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
