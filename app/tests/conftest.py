from collections.abc import AsyncGenerator, Callable
from types import SimpleNamespace
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.db.session import get_async_session, get_engine
from main import app


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = get_engine()
    if engine is None:
        raise RuntimeError("Database engine is not configured for tests.")

    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)

        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_async_session] = override_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def set_current_user() -> Callable[[set[str]], None]:
    def _set_current_user(permission_codes: set[str]) -> None:
        permissions = [SimpleNamespace(code=code) for code in permission_codes]
        role = SimpleNamespace(permissions=permissions)
        user = SimpleNamespace(id=uuid4(), roles=[role], is_active=True)
        app.dependency_overrides[get_current_user] = lambda: user

    return _set_current_user
