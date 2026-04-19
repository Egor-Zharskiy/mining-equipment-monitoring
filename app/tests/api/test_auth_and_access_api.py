from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Permission, Role, User
from app.services.security_service import SecurityService


pytestmark = pytest.mark.asyncio


async def _create_user(
    db_session: AsyncSession,
    *,
    email: str,
    password: str,
    is_active: bool = True,
) -> User:
    user = User(
        username=f"user_{uuid4().hex[:8]}",
        email=email,
        hashed_password=SecurityService.hash_password(password),
        first_name="Иван",
        last_name="Тестов",
        is_active=is_active,
        roles=[],
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


async def test_login_returns_access_token_for_active_user(client: AsyncClient, db_session: AsyncSession):
    password = "StrongPass123!"
    user = await _create_user(db_session, email=f"login_{uuid4().hex[:8]}@example.com", password=password)

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert isinstance(payload["access_token"], str)
    assert payload["access_token"]


async def test_request_id_header_is_returned(client: AsyncClient):
    request_id = f"req-{uuid4().hex}"

    response = await client.get(
        "/api/v1/permissions/",
        headers={"X-Request-ID": request_id},
    )

    assert response.headers["X-Request-ID"] == request_id


async def test_login_rejects_inactive_user(client: AsyncClient, db_session: AsyncSession):
    password = "StrongPass123!"
    user = await _create_user(
        db_session,
        email=f"inactive_{uuid4().hex[:8]}@example.com",
        password=password,
        is_active=False,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User account is inactive."


async def test_get_my_profile_requires_active_authenticated_user(client: AsyncClient, db_session: AsyncSession):
    password = "StrongPass123!"
    user = await _create_user(db_session, email=f"me_{uuid4().hex[:8]}@example.com", password=password)
    token = SecurityService.create_access_token(user_id=user.id)

    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)


async def test_get_my_profile_rejects_inactive_user_token(client: AsyncClient, db_session: AsyncSession):
    password = "StrongPass123!"
    user = await _create_user(
        db_session,
        email=f"disabled_{uuid4().hex[:8]}@example.com",
        password=password,
        is_active=False,
    )
    token = SecurityService.create_access_token(user_id=user.id)

    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authenticated user is inactive."


async def test_role_endpoints_enforce_permissions(client: AsyncClient, db_session: AsyncSession, set_current_user):
    permission = Permission(code=f"perm_{uuid4().hex[:8]}", description="Тестовое право")
    db_session.add(permission)
    await db_session.flush()

    await set_current_user({"roles.manage"})
    create_response = await client.post(
        "/api/v1/roles/",
        json={
            "name": f"role_{uuid4().hex[:8]}",
            "description": "Тестовая роль",
            "permission_ids": [str(permission.id)],
        },
    )
    assert create_response.status_code == 201
    created_role_id = create_response.json()["id"]

    await set_current_user(set())
    denied_create_response = await client.post(
        "/api/v1/roles/",
        json={
            "name": f"role_{uuid4().hex[:8]}",
            "description": "Должно быть запрещено",
            "permission_ids": [],
        },
    )
    assert denied_create_response.status_code == 403
    assert denied_create_response.json()["detail"] == "Missing permissions: roles.manage."

    await set_current_user({"roles.read"})
    list_response = await client.get("/api/v1/roles/")
    assert list_response.status_code == 200
    assert any(item["id"] == created_role_id for item in list_response.json())

    await set_current_user(set())
    denied_list_response = await client.get("/api/v1/roles/")
    assert denied_list_response.status_code == 403
    assert denied_list_response.json()["detail"] == "Missing permissions: roles.read."


async def test_permission_endpoints_enforce_permissions(client: AsyncClient, set_current_user):
    await set_current_user({"roles.manage"})
    create_response = await client.post(
        "/api/v1/permissions/",
        json={
            "code": f"catalog_{uuid4().hex[:8]}",
            "description": "Право для теста каталога",
        },
    )
    assert create_response.status_code == 201
    created_permission_code = create_response.json()["code"]

    await set_current_user(set())
    denied_create_response = await client.post(
        "/api/v1/permissions/",
        json={
            "code": f"catalog_{uuid4().hex[:8]}",
            "description": "Должно быть запрещено",
        },
    )
    assert denied_create_response.status_code == 403
    assert denied_create_response.json()["detail"] == "Missing permissions: roles.manage."

    await set_current_user({"permissions.read"})
    list_response = await client.get("/api/v1/permissions/")
    assert list_response.status_code == 200
    assert any(item["code"] == created_permission_code for item in list_response.json())

    await set_current_user(set())
    denied_list_response = await client.get("/api/v1/permissions/")
    assert denied_list_response.status_code == 403
    assert denied_list_response.json()["detail"] == "Missing permissions: permissions.read."
