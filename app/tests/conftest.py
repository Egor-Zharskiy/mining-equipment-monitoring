from collections.abc import AsyncGenerator, Callable
from types import SimpleNamespace
from uuid import uuid4

import pytest_asyncio
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.db.session import get_async_session, get_engine
from app.models import User
from app.services.security_service import SecurityService
from main import app


@pytest.fixture(autouse=True)
def prevent_real_email_delivery(monkeypatch, request):
    if request.node.path.name == "test_email_service.py":
        return

    async def fake_send_email(self, *, to_email: str, subject: str, body: str) -> bool:
        return True

    monkeypatch.setattr(
        "app.services.email_service.EmailService.send_email",
        fake_send_email,
    )


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
async def set_current_user(db_session: AsyncSession) -> Callable[[set[str]], None]:
    async def _ensure_user_exists(user_id, *, is_active: bool) -> None:
        if user_id is None:
            return

        existing_user = await db_session.get(User, user_id)
        if existing_user is not None:
            return

        user = User(
            id=user_id,
            username=f"test_user_{uuid4().hex[:10]}",
            email=f"test_user_{uuid4().hex[:10]}@example.com",
            hashed_password=SecurityService.hash_password("StrongPass123!"),
            first_name="Тестовый",
            last_name="Пользователь",
            is_active=is_active,
        )
        db_session.add(user)
        await db_session.flush()

    async def _set_current_user(
        permission_codes: set[str],
        *,
        user_id=None,
        is_active: bool = True,
    ) -> None:
        resolved_user_id = user_id or uuid4()
        await _ensure_user_exists(resolved_user_id, is_active=is_active)

        permissions = [SimpleNamespace(code=code) for code in permission_codes]
        role = SimpleNamespace(permissions=permissions)
        user = SimpleNamespace(id=resolved_user_id, roles=[role], is_active=is_active)
        app.dependency_overrides[get_current_user] = lambda: user

    return _set_current_user
