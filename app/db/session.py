from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import db_config


@lru_cache(maxsize=1)
def get_engine():
    """Create and cache the asynchronous SQLAlchemy engine."""

    if db_config.sqlalchemy_url is None:
        return None

    return create_async_engine(db_config.sqlalchemy_url)


@lru_cache(maxsize=1)
def get_async_session_maker():
    """Create and cache the async session factory."""

    engine = get_engine()
    if engine is None:
        return None

    return async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async_session_maker = get_async_session_maker()

    if async_session_maker is None:
        raise RuntimeError(
            "Database is not configured. Set SQLALCHEMY_URL, SQLALCHEMY_URL_LOCAL, or SQLALCHEMY_URL_DOCKER in .env."
        )

    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            raise
        finally:
            await session.close()
