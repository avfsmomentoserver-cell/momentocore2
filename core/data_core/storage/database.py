"""
Database Connection & Session Management.
Handles async PostgreSQL connections via SQLAlchemy.
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

# Database URL from environment (default to local dev)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://momento:momentopass@localhost:5432/momentocore"
)

# Create Async Engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",  # Debug SQL
    pool_pre_ping=True,  # Auto-reconnect
    pool_size=20,
    max_overflow=40
)

# Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base Class for Models
Base = declarative_base()

# Dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a database session for dependency injection.
    Ensures proper cleanup after request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """
    Initialize database tables (for dev/testing).
    In production, use Alembic migrations.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """Close database engine connection."""
    await engine.dispose()
