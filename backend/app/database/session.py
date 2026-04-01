"""
Database session management for StockTracker.

Provides an async SQLAlchemy engine and session factory for SQLite,
along with a FastAPI dependency for injecting DB sessions into routes.
"""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.database.models import Base

logger = logging.getLogger(__name__)

# ── Engine & Session Factory ──────────────────────────────────────────

engine = create_async_engine(
    settings.database.url,
    echo=False,
    # SQLite needs this for async writes in the same event loop
    connect_args={"check_same_thread": False},
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Lifecycle helpers ─────────────────────────────────────────────────

async def init_db() -> None:
    """
    Create all tables if they don't exist.
    Called once during application startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized.")


async def close_db() -> None:
    """
    Dispose of the engine connection pool.
    Called during application shutdown.
    """
    await engine.dispose()
    logger.info("Database engine disposed.")


# ── FastAPI Dependency ────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an async database session for use in FastAPI route handlers.

    Usage:
        @router.get("/stocks")
        async def list_stocks(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        yield session
