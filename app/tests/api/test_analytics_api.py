from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import Role, User
from app.services.security_service import SecurityService


pytestmark = pytest.mark.asyncio


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
        first_name="Аналитик",
        last_name="Пользователь",
        is_active=True,
        roles=[role],
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


async def _create_equipment_type(client, *, name_prefix: str = "Тип аналитики"):
    response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"{name_prefix} {uuid4().hex[:8]}",
            "description": "Тип оборудования для analytics stage.",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _create_parameter(client, *, code_prefix: str, name: str):
    response = await client.post(
        "/api/v1/parameters/",
        json={
            "code": f"{code_prefix}_{uuid4().hex[:8]}",
            "name": name,
            "unit": "C",
            "description": "Параметр для analytics stage.",
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


async def _create_equipment(client, equipment_type_id: str, *, code_prefix: str):
    response = await client.post(
        "/api/v1/equipment/",
        json={
            "name": f"Оборудование аналитики {uuid4().hex[:6]}",
            "code": f"{code_prefix}-{uuid4().hex[:8]}",
            "serial_number": f"AS-{uuid4().hex[:8]}",
            "equipment_type_id": equipment_type_id,
            "location": "Аналитический участок",
            "description": "Оборудование для analytics тестов.",
            "specifications": {"power_kw": 240},
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _create_reading(client, *, equipment_id: str, parameter_id: str, value: str, minutes_ago: int):
    response = await client.post(
        "/api/v1/telemetry-readings/",
        json={
            "equipment_id": equipment_id,
            "parameter_id": parameter_id,
            "value": value,
            "measured_at": (datetime.now(UTC) - timedelta(minutes=minutes_ago)).isoformat(),
        },
    )
    assert response.status_code == 201
    return response.json()


async def _create_maintenance_task(
    client,
    *,
    equipment_id: str,
    title: str,
    priority: str,
    due_at: datetime | None,
    assigned_to_user_id: str | None = None,
):
    payload = {
        "equipment_id": equipment_id,
        "title": title,
        "priority": priority,
    }
    if due_at is not None:
        payload["due_at"] = due_at.isoformat()
    if assigned_to_user_id is not None:
        payload["assigned_to_user_id"] = assigned_to_user_id

    response = await client.post("/api/v1/maintenance-tasks/", json=payload)
    assert response.status_code == 201
    return response.json()


async def test_analytics_dashboard_endpoints_return_expected_aggregates(client, db_session, set_current_user):
    recipient = await _create_user_with_role(db_session, email_prefix="analytics_manager", role_name="manager")

    setup_permissions = {
        "analytics.read",
        "equipment.read",
        "equipment.manage",
        "maintenance.read",
        "maintenance.manage",
        "notifications.manage",
        "telemetry.create",
        "telemetry.read",
        "threshold_rules.read",
        "threshold_rules.manage",
    }
    await set_current_user(setup_permissions)

    baseline_overview_response = await client.get("/api/v1/analytics/overview?days=30")
    assert baseline_overview_response.status_code == 200
    baseline_overview = baseline_overview_response.json()

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, code_prefix="analytics_temp", name="Температура двигателя")
    await _create_binding(client, equipment_type_id, parameter_id)
    await _create_threshold_rule(client, equipment_type_id, parameter_id)

    critical_equipment_id = await _create_equipment(client, equipment_type_id, code_prefix="AN-CRIT")
    normal_equipment_id = await _create_equipment(client, equipment_type_id, code_prefix="AN-NORM")
    unknown_equipment_id = await _create_equipment(client, equipment_type_id, code_prefix="AN-UNKN")

    await _create_reading(
        client,
        equipment_id=critical_equipment_id,
        parameter_id=parameter_id,
        value="70.0",
        minutes_ago=3,
    )
    await _create_reading(
        client,
        equipment_id=critical_equipment_id,
        parameter_id=parameter_id,
        value="99.0",
        minutes_ago=1,
    )
    await _create_reading(
        client,
        equipment_id=normal_equipment_id,
        parameter_id=parameter_id,
        value="65.0",
        minutes_ago=2,
    )

    baseline_maintenance_analytics_response = await client.get("/api/v1/analytics/maintenance")
    assert baseline_maintenance_analytics_response.status_code == 200
    baseline_maintenance_analytics = baseline_maintenance_analytics_response.json()

    await _create_maintenance_task(
        client,
        equipment_id=unknown_equipment_id,
        title="Просроченное ТО",
        priority="medium",
        due_at=datetime.now(UTC) - timedelta(days=1),
    )
    await _create_maintenance_task(
        client,
        equipment_id=critical_equipment_id,
        title="Скорое ТО",
        priority="high",
        due_at=datetime.now(UTC) + timedelta(days=2),
        assigned_to_user_id=str(recipient.id),
    )
    completed_task = await _create_maintenance_task(
        client,
        equipment_id=normal_equipment_id,
        title="Выполненное ТО",
        priority="low",
        due_at=None,
    )
    complete_response = await client.post(
        f"/api/v1/maintenance-tasks/{completed_task['id']}/complete",
        json={
            "summary": "ТО выполнено",
            "details": "Проверка и смазка завершены.",
            "performed_at": datetime.now(UTC).isoformat(),
            "performed_by_user_id": str(recipient.id),
        },
    )
    assert complete_response.status_code == 201

    overview_before_manual_notification_response = await client.get("/api/v1/analytics/overview?days=30")
    assert overview_before_manual_notification_response.status_code == 200
    overview_before_manual_notification = overview_before_manual_notification_response.json()
    recipient_notifications_before_manual_response = await client.get(
        f"/api/v1/analytics/notifications?recipient_user_id={recipient.id}"
    )
    assert recipient_notifications_before_manual_response.status_code == 200
    recipient_notifications_before_manual = recipient_notifications_before_manual_response.json()

    manual_notification_response = await client.post(
        "/api/v1/notifications/manual",
        json={
            "recipient_user_ids": [str(recipient.id)],
            "channels": ["internal"],
            "title": "Ручное уведомление",
            "message": "Проверьте участок аналитики.",
        },
    )
    assert manual_notification_response.status_code == 201

    await set_current_user({"notifications.read"}, user_id=recipient.id)
    internal_notifications_response = await client.get("/api/v1/notifications/")
    assert internal_notifications_response.status_code == 200
    manual_notification = next(
        item for item in internal_notifications_response.json() if item["notification_type"] == "manual"
    )
    mark_read_response = await client.post(f"/api/v1/notifications/{manual_notification['id']}/read")
    assert mark_read_response.status_code == 200

    await set_current_user({"analytics.read"}, user_id=recipient.id)

    overview_response = await client.get("/api/v1/analytics/overview?days=30")
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert overview["equipment"]["total_count"] - baseline_overview["equipment"]["total_count"] == 3
    assert (
        overview["equipment"]["buckets"]["critical"] - baseline_overview["equipment"]["buckets"]["critical"]
        == 1
    )
    assert overview["equipment"]["buckets"]["normal"] - baseline_overview["equipment"]["buckets"]["normal"] == 1
    assert overview["equipment"]["buckets"]["unknown"] - baseline_overview["equipment"]["buckets"]["unknown"] == 1
    assert overview["events"]["total_count"] - baseline_overview["events"]["total_count"] == 2
    assert overview["events"]["buckets"]["critical"] - baseline_overview["events"]["buckets"]["critical"] == 2
    assert overview["maintenance"]["total_count"] - baseline_overview["maintenance"]["total_count"] == 3
    assert overview["maintenance"]["buckets"]["open"] - baseline_overview["maintenance"]["buckets"]["open"] == 2
    assert overview["maintenance"]["buckets"]["done"] - baseline_overview["maintenance"]["buckets"]["done"] == 1
    assert (
        overview["notifications"]["total_count"]
        - overview_before_manual_notification["notifications"]["total_count"]
        == 1
    )
    assert (
        overview["notifications"]["buckets"]["internal"]
        - overview_before_manual_notification["notifications"]["buckets"]["internal"]
        == 1
    )
    assert (
        overview["notifications"]["buckets"]["email"]
        - overview_before_manual_notification["notifications"]["buckets"]["email"]
        == 0
    )

    equipment_status_response = await client.get(
        f"/api/v1/analytics/equipment-status?equipment_type_id={equipment_type_id}"
    )
    assert equipment_status_response.status_code == 200
    equipment_status = equipment_status_response.json()
    assert equipment_status["total_count"] == 3
    assert equipment_status["by_status"]["critical"] == 1
    assert equipment_status["by_status"]["normal"] == 1
    assert equipment_status["by_status"]["unknown"] == 1
    assert len(equipment_status["by_type"]) == 1
    assert equipment_status["by_type"][0]["total_count"] == 3
    assert equipment_status["by_type"][0]["by_status"]["unknown"] == 1

    event_analytics_response = await client.get(
        f"/api/v1/analytics/events?equipment_id={critical_equipment_id}&severity=critical"
    )
    assert event_analytics_response.status_code == 200
    event_analytics = event_analytics_response.json()
    assert event_analytics["total_count"] == 2
    assert event_analytics["by_severity"]["critical"] == 2
    assert event_analytics["by_event_type"]["parameter_critical"] == 1
    assert event_analytics["by_event_type"]["equipment_critical"] == 1
    assert len(event_analytics["timeline"]) == 1
    assert event_analytics["timeline"][0]["count"] == 2

    telemetry_history_response = await client.get(
        f"/api/v1/analytics/telemetry-history?equipment_id={critical_equipment_id}&parameter_id={parameter_id}"
    )
    assert telemetry_history_response.status_code == 200
    telemetry_history = telemetry_history_response.json()
    assert telemetry_history["equipment"]["id"] == critical_equipment_id
    assert telemetry_history["parameter"]["id"] == parameter_id
    assert telemetry_history["summary"]["point_count"] == 2
    assert telemetry_history["summary"]["min_value"] == "70.0000"
    assert telemetry_history["summary"]["max_value"] == "99.0000"
    assert telemetry_history["points"][0]["status"] == "normal"
    assert telemetry_history["points"][1]["status"] == "critical"

    maintenance_analytics_response = await client.get("/api/v1/analytics/maintenance")
    assert maintenance_analytics_response.status_code == 200
    maintenance_analytics = maintenance_analytics_response.json()
    assert maintenance_analytics["total_count"] - baseline_maintenance_analytics["total_count"] == 3
    assert maintenance_analytics["by_status"]["open"] - baseline_maintenance_analytics["by_status"]["open"] == 2
    assert maintenance_analytics["by_status"]["done"] - baseline_maintenance_analytics["by_status"]["done"] == 1
    assert maintenance_analytics["by_priority"]["high"] - baseline_maintenance_analytics["by_priority"]["high"] == 1
    assert maintenance_analytics["overdue_count"] - baseline_maintenance_analytics["overdue_count"] == 1
    assert maintenance_analytics["upcoming_count"] - baseline_maintenance_analytics["upcoming_count"] == 1
    assert maintenance_analytics["completed_count"] - baseline_maintenance_analytics["completed_count"] == 1

    notifications_analytics_response = await client.get(
        f"/api/v1/analytics/notifications?recipient_user_id={recipient.id}"
    )
    assert notifications_analytics_response.status_code == 200
    notifications_analytics = notifications_analytics_response.json()
    assert notifications_analytics["total_count"] - recipient_notifications_before_manual["total_count"] == 1
    assert notifications_analytics["unread_count"] - recipient_notifications_before_manual["unread_count"] == 0
    assert (
        notifications_analytics["by_channel"]["internal"]
        - recipient_notifications_before_manual["by_channel"]["internal"]
        == 1
    )
    assert (
        notifications_analytics["by_channel"]["email"]
        - recipient_notifications_before_manual["by_channel"]["email"]
        == 0
    )
    assert notifications_analytics["by_type"]["manual"] - recipient_notifications_before_manual["by_type"]["manual"] == 1
    assert (
        notifications_analytics["by_read_state"]["read"]
        - recipient_notifications_before_manual["by_read_state"]["read"]
        == 1
    )
    assert (
        notifications_analytics["by_read_state"]["unread"]
        - recipient_notifications_before_manual["by_read_state"]["unread"]
        == 0
    )


async def test_analytics_equipment_status_counts_unknown_items_without_current_state(client, set_current_user):
    await set_current_user({"analytics.read", "equipment.read", "equipment.manage"})

    equipment_type_id = await _create_equipment_type(client, name_prefix="Unknown аналитика")
    await _create_equipment(client, equipment_type_id, code_prefix="AN-EMPTY")

    response = await client.get(f"/api/v1/analytics/equipment-status?equipment_type_id={equipment_type_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_count"] == 1
    assert payload["by_status"]["unknown"] == 1
    assert payload["by_status"]["normal"] == 0


async def test_analytics_telemetry_history_returns_empty_series_for_valid_filter_without_data(client, set_current_user):
    await set_current_user({"analytics.read", "equipment.read", "equipment.manage"})

    equipment_type_id = await _create_equipment_type(client, name_prefix="История без данных")
    parameter_id = await _create_parameter(client, code_prefix="analytics_empty", name="Температура без истории")
    equipment_id = await _create_equipment(client, equipment_type_id, code_prefix="AN-NODATA")

    response = await client.get(
        f"/api/v1/analytics/telemetry-history?equipment_id={equipment_id}&parameter_id={parameter_id}"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["point_count"] == 0
    assert payload["summary"]["min_value"] is None
    assert payload["summary"]["max_value"] is None
    assert payload["summary"]["avg_value"] is None
    assert payload["points"] == []


async def test_analytics_endpoints_require_analytics_read_permission(client, set_current_user):
    await set_current_user(set())

    overview_response = await client.get("/api/v1/analytics/overview")
    events_response = await client.get("/api/v1/analytics/events")

    assert overview_response.status_code == 403
    assert overview_response.json()["detail"] == "Missing permissions: analytics.read."
    assert events_response.status_code == 403
    assert events_response.json()["detail"] == "Missing permissions: analytics.read."


async def test_analytics_events_reject_invalid_date_range_and_unknown_filters(client, db_session, set_current_user):
    recipient = await _create_user_with_role(db_session, email_prefix="analytics_filter_user", role_name="manager")
    await set_current_user({"analytics.read"})

    invalid_range_response = await client.get(
        "/api/v1/analytics/events?"
        "date_from=2026-03-10T00:00:00Z&date_to=2026-03-01T00:00:00Z"
    )
    assert invalid_range_response.status_code == 400
    assert (
        invalid_range_response.json()["detail"]
        == "Invalid date range: date_from must be less than or equal to date_to."
    )

    invalid_severity_response = await client.get("/api/v1/analytics/events?severity=offline")
    assert invalid_severity_response.status_code == 400
    assert invalid_severity_response.json()["detail"] == "Unsupported event severity filter."

    unknown_recipient_response = await client.get(
        f"/api/v1/analytics/notifications?recipient_user_id={uuid4()}"
    )
    assert unknown_recipient_response.status_code == 400
    assert unknown_recipient_response.json()["detail"] == "Notification analytics references an unknown recipient user."

    valid_recipient_response = await client.get(
        f"/api/v1/analytics/notifications?recipient_user_id={recipient.id}"
    )
    assert valid_recipient_response.status_code == 200
    assert valid_recipient_response.json()["total_count"] == 0


async def test_analytics_rejects_unknown_equipment_type_and_telemetry_entities(client, set_current_user):
    await set_current_user({"analytics.read"})

    equipment_type_response = await client.get(f"/api/v1/analytics/equipment-status?equipment_type_id={uuid4()}")
    telemetry_response = await client.get(
        f"/api/v1/analytics/telemetry-history?equipment_id={uuid4()}&parameter_id={uuid4()}"
    )

    assert equipment_type_response.status_code == 400
    assert (
        equipment_type_response.json()["detail"]
        == "Equipment type filter references an unknown equipment type."
    )
    assert telemetry_response.status_code == 400
    assert telemetry_response.json()["detail"] == "Telemetry history references an unknown equipment item."
