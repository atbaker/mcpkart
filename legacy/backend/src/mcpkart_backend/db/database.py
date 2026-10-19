"""Database configuration and session management."""

import os
from collections.abc import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

# Sync database URL (for Alembic migrations only)
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://mcpkart:mcpkart_dev@localhost:5432/mcpkart"
)

# Async database URL (for FastAPI and Temporal activities)
ASYNC_DATABASE_URL = os.environ.get(
    "ASYNC_DATABASE_URL", "postgresql+asyncpg://mcpkart:mcpkart_dev@localhost:5432/mcpkart"
)

# Sync engine (for Alembic migrations only)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine (for application code)
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting sync database sessions (Alembic only)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        yield session
