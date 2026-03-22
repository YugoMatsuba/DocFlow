from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import asyncio
from typing import AsyncGenerator

from .base import Base
from config.settings import settings

# Import models to register them with SQLAlchemy metadata
from .models.workflow import WorkflowModel, NodeModel  # noqa: F401
from .models.execution import WorkflowExecutionModel  # noqa: F401

# Create engines using settings
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True,
)

sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    echo=True,
)

# Session makers
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session for FastAPI dependency injection"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_sync_session():
    """Get sync database session"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

async def create_tables():
    """Initialize database tables"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def init_db():
    """Initialize database"""
    await create_tables()