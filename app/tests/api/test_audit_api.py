from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Role, User
from app.services.security_service import SecurityService


pytestmark = pytest.mark.asyncio


async def _get_role(db_session: AsyncSession, role_name: str) -> Role:
    result = await db_session.execute(select(Role).where(Role.name == role_name))
    role = result.scalar_one_or_none()
    assert role is not None
    return role


async def _create_user_with_role(
    db_session: AsyncSession,
    *,
    role_name: str,
    email_prefix: str,
    password: str = "StrongPass123!",
) -> User:
    role = await _get_role(db_session, role_name)
    user = User(
        username=f"user_{uuid4().hex[:8]}",
        email=f"{email_prefix}_{uuid4().hex[:8]}@example.com",
        hashed_password=SecurityService.hash_password(password),
        first_name="Аудит",
        last_name="Пользователь",
        is_active=True,
        roles=[role],
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


async def _login(client, *, email: str, password: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def _create_equipment_type(client, headers: dict[str, str]) -> str:
    response = await client.post(
        "/api/v1/equipment-types/",
        headers=headers,
        json={
            "name": f"Аудит тип {uuid4().hex[:8]}",
            "description": "Тип оборудования для audit stage.",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def test_audit_logs_capture_login_and_equipment_mutations(client, db_session: AsyncSession):
    password = "StrongPass123!"
    admin_user = await _create_user_with_role(
        db_session,
        role_name="admin",
        email_prefix="audit_admin",
        password=password,
    )
    headers = await _login(client, email=admin_user.email, password=password)

    equipment_type_id = await _create_equipment_type(client, headers)
    create_response = await client.post(
        "/api/v1/equipment/",
        headers=headers,
        json={
            "name": "Аудит экскаватор",
            "code": f"AUD-EQ-{uuid4().hex[:8]}",
            "serial_number": f"AUD-SN-{uuid4().hex[:8]}",
            "equipment_type_id": equipment_type_id,
            "location": "Карьер аудита",
            "description": "Оборудование для проверки audit logs.",
            "specifications": {"power_kw": 320},
            "is_active": True,
        },
    )
    assert create_response.status_code == 201
    equipment_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/equipment/{equipment_id}",
        headers=headers,
        json={"description": "Обновленное описание аудита."},
    )
    assert update_response.status_code == 200

    delete_response = await client.delete(f"/api/v1/equipment/{equipment_id}", headers=headers)
    assert delete_response.status_code == 204

    audit_response = await client.get(
        f"/api/v1/audit-logs/?actor_user_id={admin_user.id}&resource_type=equipment",
        headers=headers,
    )
    assert audit_response.status_code == 200
    payload = audit_response.json()
    assert len(payload) == 3
    assert {item["action"] for item in payload} == {"create", "update", "delete"}
    assert all(item["resource_id"] == equipment_id for item in payload)
    assert all(item["actor_user"]["id"] == str(admin_user.id) for item in payload)
    create_log = next(item for item in payload if item["action"] == "create")
    assert create_log["details"]["request"]["description"] == "Оборудование для проверки audit logs."

    login_audit_response = await client.get(
        f"/api/v1/audit-logs/?actor_user_id={admin_user.id}&action=login&resource_type=auth",
        headers=headers,
    )
    assert login_audit_response.status_code == 200
    login_payload = login_audit_response.json()
    assert len(login_payload) == 1
    assert login_payload[0]["resource_id"] == str(admin_user.id)
    assert login_payload[0]["details"]["request"]["email"] == admin_user.email
    assert login_payload[0]["details"]["request"]["password"] == "***"


async def test_audit_logs_do_not_record_failed_mutations(client, db_session: AsyncSession):
    password = "StrongPass123!"
    admin_user = await _create_user_with_role(
        db_session,
        role_name="admin",
        email_prefix="audit_fail_admin",
        password=password,
    )
    headers = await _login(client, email=admin_user.email, password=password)

    equipment_type_name = f"Аудит дубликат {uuid4().hex[:8]}"
    first_response = await client.post(
        "/api/v1/equipment-types/",
        headers=headers,
        json={"name": equipment_type_name, "description": "Первый тип", "is_active": True},
    )
    assert first_response.status_code == 201

    baseline_logs_response = await client.get(
        f"/api/v1/audit-logs/?actor_user_id={admin_user.id}&resource_type=equipment_types",
        headers=headers,
    )
    assert baseline_logs_response.status_code == 200
    baseline_count = len(baseline_logs_response.json())

    duplicate_response = await client.post(
        "/api/v1/equipment-types/",
        headers=headers,
        json={"name": equipment_type_name, "description": "Дубликат", "is_active": True},
    )
    assert duplicate_response.status_code == 400

    after_logs_response = await client.get(
        f"/api/v1/audit-logs/?actor_user_id={admin_user.id}&resource_type=equipment_types",
        headers=headers,
    )
    assert after_logs_response.status_code == 200
    assert len(after_logs_response.json()) == baseline_count


async def test_audit_log_list_and_detail_require_permission(client, set_current_user):
    await set_current_user(set())

    list_response = await client.get("/api/v1/audit-logs/")
    detail_response = await client.get(f"/api/v1/audit-logs/{uuid4()}")

    assert list_response.status_code == 403
    assert list_response.json()["detail"] == "Missing permissions: audit.read."
    assert detail_response.status_code == 403
    assert detail_response.json()["detail"] == "Missing permissions: audit.read."


async def test_audit_logs_support_filters_and_date_validation(client, db_session: AsyncSession):
    password = "StrongPass123!"
    admin_user = await _create_user_with_role(
        db_session,
        role_name="admin",
        email_prefix="audit_filter_admin",
        password=password,
    )
    headers = await _login(client, email=admin_user.email, password=password)
    equipment_type_id = await _create_equipment_type(client, headers)

    create_response = await client.post(
        "/api/v1/equipment/",
        headers=headers,
        json={
            "name": "Фильтр аудит",
            "code": f"AUD-FLT-{uuid4().hex[:8]}",
            "serial_number": f"AUD-FLT-SN-{uuid4().hex[:8]}",
            "equipment_type_id": equipment_type_id,
            "location": "Карьер фильтра",
            "description": "Оборудование для фильтрации аудита.",
            "specifications": {"power_kw": 200},
            "is_active": True,
        },
    )
    assert create_response.status_code == 201
    equipment_id = create_response.json()["id"]

    filtered_response = await client.get(
        f"/api/v1/audit-logs/?resource_type=equipment&resource_id={equipment_id}&limit=5",
        headers=headers,
    )
    assert filtered_response.status_code == 200
    payload = filtered_response.json()
    assert len(payload) == 1
    assert payload[0]["action"] == "create"
    audit_log_id = payload[0]["id"]

    detail_response = await client.get(f"/api/v1/audit-logs/{audit_log_id}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == audit_log_id

    invalid_date_range_response = await client.get(
        "/api/v1/audit-logs/?"
        "date_from=2026-04-02T00:00:00Z&"
        "date_to=2026-03-31T00:00:00Z",
        headers=headers,
    )
    assert invalid_date_range_response.status_code == 400
    assert (
        invalid_date_range_response.json()["detail"]
        == "Invalid date range: date_from must be less than or equal to date_to."
    )


async def test_get_audit_log_returns_404_for_unknown_id(client, set_current_user):
    await set_current_user({"audit.read"})

    response = await client.get(f"/api/v1/audit-logs/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Audit log not found."
