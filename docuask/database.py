"""Database connection and session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from docuask.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


settings = get_settings()


@lru_cache
def get_engine():
    """Return the lazily-created async SQLAlchemy engine."""
    return create_async_engine(
        settings.database_url or settings.generate_database_url(),
        echo=False,
        pool_pre_ping=True,
    )


@lru_cache
def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Return the cached async session factory."""
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for FastAPI dependency injection."""
    async_session_maker = get_session_maker()
    async with async_session_maker() as session:
        yield session


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for non-FastAPI call sites."""
    async_session_maker = get_session_maker()
    async with async_session_maker() as session:
        yield session


async def init_db() -> None:
    """Create database tables for registered models."""
    import docuask.models  # noqa: F401

    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose of database connections."""
    await get_engine().dispose()
    get_session_maker.cache_clear()
    get_engine.cache_clear()
