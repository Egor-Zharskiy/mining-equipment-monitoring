from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from types import SimpleNamespace
from sqlalchemy import select

from app.models import Role, User
from app.services.security_service import SecurityService


pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def prevent_real_email_delivery(monkeypatch):
    async def fake_send_email(self, *, to_email: str, subject: str, body: str) -> bool:
        return True

    monkeypatch.setattr(
        "app.services.email_service.EmailService.send_email",
        fake_send_email,
    )


async def _get_role(db_session, role_name: str) -> Role:
    result = await db_session.execute(select(Role).where(Role.name == role_name))
    role = result.scalar_one_or_none()
    assert role is not None
    return role


async def _create_user_with_role(db_session, *, email_prefix: str, role_name: str) -> User:
    role = await _get_role(db_session, role_name)
    user = User(
        username=f"user_{uuid4().hex[:8]}",
        email=f"{email_prefix}_{uuid4().hex[:8]}@example.com",
        hashed_password=SecurityService.hash_password("StrongPass123!"),
        first_name="Увед",
        last_name="Пользователь",
        is_active=True,
        roles=[role],
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


async def _create_equipment_type(client):
    response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Тип уведомлений {uuid4().hex[:8]}",
            "description": "Тип оборудования для notifications stage.",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _create_parameter(client, code_prefix: str, name: str):
    response = await client.post(
        "/api/v1/parameters/",
        json={
            "code": f"{code_prefix}_{uuid4().hex[:8]}",
            "name": name,
            "unit": "C",
            "description": "Параметр для notifications stage.",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _create_binding(client, equipment_type_id: str, parameter_id: str):
    response = await client.post(
        "/api/v1/equipment-type-parameters/",
        json={
            "equipment_type_id": equipment_type_id,
            "parameter_id": parameter_id,
            "is_required": True,
        },
    )
    assert response.status_code == 201


async def _create_threshold_rule(client, equipment_type_id: str, parameter_id: str):
    response = await client.post(
        "/api/v1/threshold-rules/",
        json={
            "equipment_type_id": equipment_type_id,
            "parameter_id": parameter_id,
            "warning_max": "80.0",
            "critical_max": "95.0",
            "is_active": True,
        },
    )
    assert response.status_code == 201


async def _create_equipment(client, equipment_type_id: str):
    response = await client.post(
        "/api/v1/equipment/",
        json={
            "name": f"Оборудование уведомлений {uuid4().hex[:6]}",
            "code": f"NT-{uuid4().hex[:8]}",
            "serial_number": f"NS-{uuid4().hex[:8]}",
            "equipment_type_id": equipment_type_id,
            "location": "Карьер уведомлений",
            "description": "Оборудование для проверки notifications pipeline.",
            "specifications": {"power_kw": 210},
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def test_critical_event_does_not_create_notifications_when_runtime_pipeline_is_disabled(client, db_session, set_current_user, monkeypatch):
    monkeypatch.setattr(
        "app.services.notification_service.app_config",
        SimpleNamespace(runtime_notifications_enabled=False),
    )
    recipient = await _create_user_with_role(db_session, email_prefix="notif_manager", role_name="manager")
    actor = await _create_user_with_role(db_session, email_prefix="notif_actor", role_name="technician")
    await set_current_user(
        {
            "equipment.read",
            "equipment.manage",
            "telemetry.create",
            "telemetry.read",
            "threshold_rules.manage",
            "threshold_rules.read",
            "notifications.read",
        },
        user_id=recipient.id,
    )

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, "notif_critical", "Температура ротора")
    await _create_binding(client, equipment_type_id, parameter_id)
    await _create_threshold_rule(client, equipment_type_id, parameter_id)
    equipment_id = await _create_equipment(client, equipment_type_id)

    await set_current_user(
        {
            "equipment.read",
            "equipment.manage",
            "telemetry.create",
            "telemetry.read",
            "threshold_rules.manage",
            "threshold_rules.read",
            "maintenance.read",
            "maintenance.manage",
            "events.read",
        },
        user_id=actor.id,
    )
    reading_response = await client.post(
        "/api/v1/telemetry-readings/",
        json={
            "equipment_id": equipment_id,
            "parameter_id": parameter_id,
            "value": "99.0",
            "measured_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
        },
    )
    assert reading_response.status_code == 201

    await set_current_user({"notifications.read"}, user_id=recipient.id)
    internal_response = await client.get("/api/v1/notifications/")
    assert internal_response.status_code == 200
    internal_payload = internal_response.json()
    assert internal_payload == []

    email_response = await client.get("/api/v1/notifications/?channel=email")
    assert email_response.status_code == 200
    email_payload = email_response.json()
    assert email_payload == []


async def test_upcoming_maintenance_task_does_not_create_notification_when_runtime_pipeline_is_disabled(client, db_session, set_current_user, monkeypatch):
    monkeypatch.setattr(
        "app.services.notification_service.app_config",
        SimpleNamespace(runtime_notifications_enabled=False),
    )
    assignee = await _create_user_with_role(db_session, email_prefix="notif_assignee", role_name="manager")
    actor = await _create_user_with_role(db_session, email_prefix="notif_maint_actor", role_name="technician")

    await set_current_user(
        {"equipment.read", "equipment.manage", "maintenance.read", "maintenance.manage"},
        user_id=actor.id,
    )
    equipment_type_id = await _create_equipment_type(client)
    equipment_id = await _create_equipment(client, equipment_type_id)

    task_response = await client.post(
        "/api/v1/maintenance-tasks/",
        json={
            "equipment_id": equipment_id,
            "title": "Скорое обслуживание",
            "priority": "high",
            "due_at": (datetime.now(UTC) + timedelta(days=2)).isoformat(),
            "assigned_to_user_id": str(assignee.id),
        },
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    await set_current_user({"notifications.read"}, user_id=assignee.id)
    notifications_response = await client.get("/api/v1/notifications/")
    assert notifications_response.status_code == 200
    payload = notifications_response.json()
    assert payload == []


async def test_manual_notification_flow_with_mark_read_and_unread_count(client, db_session, set_current_user):
    recipient = await _create_user_with_role(db_session, email_prefix="notif_manual_recipient", role_name="manager")
    actor = await _create_user_with_role(db_session, email_prefix="notif_manual_actor", role_name="admin")

    await set_current_user({"notifications.manage"}, user_id=actor.id)
    create_response = await client.post(
        "/api/v1/notifications/manual",
        json={
            "recipient_user_ids": [str(recipient.id)],
            "channels": ["internal", "email"],
            "title": "Ручное уведомление",
            "message": "Проверьте состояние участка.",
        },
    )
    assert create_response.status_code == 201
    assert len(create_response.json()) == 2

    await set_current_user({"notifications.read"}, user_id=recipient.id)
    unread_response = await client.get("/api/v1/notifications/unread-count")
    assert unread_response.status_code == 200
    assert unread_response.json()["unread_count"] == 1

    list_response = await client.get("/api/v1/notifications/")
    assert list_response.status_code == 200
    notifications = list_response.json()
    assert len(notifications) == 1
    notification_id = notifications[0]["id"]
    assert notifications[0]["channel"] == "internal"
    assert notifications[0]["notification_type"] == "manual"

    mark_read_response = await client.post(f"/api/v1/notifications/{notification_id}/read")
    assert mark_read_response.status_code == 200
    assert mark_read_response.json()["is_read"] is True

    unread_after_response = await client.get("/api/v1/notifications/unread-count")
    assert unread_after_response.status_code == 200
    assert unread_after_response.json()["unread_count"] == 0

    read_list_response = await client.get("/api/v1/notifications/?is_read=true")
    assert read_list_response.status_code == 200
    assert len(read_list_response.json()) == 1


async def test_critical_event_creates_automatic_email_notification(client, db_session, set_current_user, monkeypatch):
    sent_emails = []

    async def fake_send_email(self, *, to_email: str, subject: str, body: str) -> bool:
        sent_emails.append({"to_email": to_email, "subject": subject, "body": body})
        return True

    monkeypatch.setattr(
        "app.services.notification_service.app_config",
        SimpleNamespace(runtime_notifications_enabled=True),
    )
    monkeypatch.setattr(
        "app.services.email_service.EmailService.send_email",
        fake_send_email,
    )

    recipient = await _create_user_with_role(db_session, email_prefix="notif_auto_recipient", role_name="manager")
    actor = await _create_user_with_role(db_session, email_prefix="notif_auto_actor", role_name="technician")

    await set_current_user(
        {
            "equipment.read",
            "equipment.manage",
            "telemetry.create",
            "telemetry.read",
            "threshold_rules.manage",
            "threshold_rules.read",
        },
        user_id=actor.id,
    )
    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, "notif_auto_critical", "Температура двигателя")
    await _create_binding(client, equipment_type_id, parameter_id)
    await _create_threshold_rule(client, equipment_type_id, parameter_id)
    equipment_id = await _create_equipment(client, equipment_type_id)

    reading_response = await client.post(
        "/api/v1/telemetry-readings/",
        json={
            "equipment_id": equipment_id,
            "parameter_id": parameter_id,
            "value": "99.0",
            "measured_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
        },
    )
    assert reading_response.status_code == 201

    await set_current_user({"notifications.read"}, user_id=recipient.id)
    email_response = await client.get("/api/v1/notifications/?channel=email")
    assert email_response.status_code == 200
    email_payload = email_response.json()
    assert len(email_payload) >= 1
    assert email_payload[0]["channel"] == "email"
    assert email_payload[0]["delivered_at"] is not None
    assert sent_emails
    assert recipient.email in {email["to_email"] for email in sent_emails}


async def test_notification_read_access_is_limited_to_recipient(client, db_session, set_current_user):
    first_user = await _create_user_with_role(db_session, email_prefix="notif_owner", role_name="manager")
    second_user = await _create_user_with_role(db_session, email_prefix="notif_other", role_name="manager")
    actor = await _create_user_with_role(db_session, email_prefix="notif_admin", role_name="admin")

    await set_current_user({"notifications.manage"}, user_id=actor.id)
    create_response = await client.post(
        "/api/v1/notifications/manual",
        json={
            "recipient_user_ids": [str(first_user.id)],
            "channels": ["internal"],
            "title": "Частное уведомление",
            "message": "Только для одного пользователя.",
        },
    )
    assert create_response.status_code == 201
    notification_id = create_response.json()[0]["id"]

    await set_current_user({"notifications.read"}, user_id=second_user.id)
    get_response = await client.get(f"/api/v1/notifications/{notification_id}")
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Notification not found."


async def test_notification_endpoints_enforce_access_control(client, db_session, set_current_user):
    recipient = await _create_user_with_role(db_session, email_prefix="notif_acl", role_name="manager")

    await set_current_user(set(), user_id=recipient.id)
    list_response = await client.get("/api/v1/notifications/")
    assert list_response.status_code == 403
    assert list_response.json()["detail"] == "Missing permissions: notifications.read."

    mark_read_response = await client.post(f"/api/v1/notifications/{uuid4()}/read")
    assert mark_read_response.status_code == 403
    assert mark_read_response.json()["detail"] == "Missing permissions: notifications.read."

    manual_response = await client.post(
        "/api/v1/notifications/manual",
        json={
            "recipient_user_ids": [str(recipient.id)],
            "channels": ["internal"],
            "title": "Запрещено",
            "message": "Недостаточно прав.",
        },
    )
    assert manual_response.status_code == 403
    assert manual_response.json()["detail"] == "Missing permissions: notifications.manage."


async def test_notification_filters_reject_invalid_values(client, db_session, set_current_user):
    recipient = await _create_user_with_role(db_session, email_prefix="notif_filters", role_name="manager")
    await set_current_user({"notifications.read"}, user_id=recipient.id)

    invalid_channel_response = await client.get("/api/v1/notifications/?channel=sms")
    assert invalid_channel_response.status_code == 400
    assert invalid_channel_response.json()["detail"] == "Unsupported notification channel filter."

    invalid_type_response = await client.get("/api/v1/notifications/?notification_type=escalation")
    assert invalid_type_response.status_code == 400
    assert invalid_type_response.json()["detail"] == "Unsupported notification type filter."

    invalid_unread_count_channel = await client.get("/api/v1/notifications/unread-count?channel=sms")
    assert invalid_unread_count_channel.status_code == 400
    assert invalid_unread_count_channel.json()["detail"] == "Unsupported notification channel filter."


async def test_manual_notification_create_rejects_invalid_channel_and_unknown_recipient(client, db_session, set_current_user):
    actor = await _create_user_with_role(db_session, email_prefix="notif_invalid_manual", role_name="admin")
    await set_current_user({"notifications.manage"}, user_id=actor.id)

    invalid_channel_response = await client.post(
        "/api/v1/notifications/manual",
        json={
            "recipient_user_ids": [str(uuid4())],
            "channels": ["sms"],
            "title": "Некорректный канал",
            "message": "Канал не поддерживается.",
        },
    )
    assert invalid_channel_response.status_code == 400
    assert invalid_channel_response.json()["detail"] == "Unsupported notification channel."

    unknown_recipient_response = await client.post(
        "/api/v1/notifications/manual",
        json={
            "recipient_user_ids": [str(uuid4())],
            "channels": ["internal"],
            "title": "Неизвестный получатель",
            "message": "Получатель не существует.",
        },
    )
    assert unknown_recipient_response.status_code == 400
    assert unknown_recipient_response.json()["detail"] == "One or more notification recipients were not found."


async def test_upcoming_maintenance_notification_pipeline_stays_disabled_on_task_update(client, db_session, set_current_user, monkeypatch):
    monkeypatch.setattr(
        "app.services.notification_service.app_config",
        SimpleNamespace(runtime_notifications_enabled=False),
    )
    assignee = await _create_user_with_role(db_session, email_prefix="notif_dedupe_assignee", role_name="manager")
    actor = await _create_user_with_role(db_session, email_prefix="notif_dedupe_actor", role_name="technician")

    await set_current_user({"equipment.read", "equipment.manage", "maintenance.read", "maintenance.manage"}, user_id=actor.id)
    equipment_type_id = await _create_equipment_type(client)
    equipment_id = await _create_equipment(client, equipment_type_id)

    create_task_response = await client.post(
        "/api/v1/maintenance-tasks/",
        json={
            "equipment_id": equipment_id,
            "title": "Обслуживание без дублей",
            "priority": "medium",
            "due_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            "assigned_to_user_id": str(assignee.id),
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    update_task_response = await client.patch(
        f"/api/v1/maintenance-tasks/{task_id}",
        json={
            "description": "Обновленное описание без повторной нотификации.",
        },
    )
    assert update_task_response.status_code == 200

    await set_current_user({"notifications.read"}, user_id=assignee.id)
    internal_notifications_response = await client.get("/api/v1/notifications/")
    assert internal_notifications_response.status_code == 200
    payload = internal_notifications_response.json()
    assert payload == []
