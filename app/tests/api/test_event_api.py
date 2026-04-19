from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest


pytestmark = pytest.mark.asyncio


async def _create_equipment_type(client):
    response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Тип событий {uuid4().hex[:8]}",
            "description": "Тип оборудования для Stage 7.",
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
            "description": "Параметр для Stage 7.",
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


async def _create_threshold_rule(
    client,
    equipment_type_id: str,
    parameter_id: str,
    *,
    warning_max: str,
    critical_max: str,
):
    response = await client.post(
        "/api/v1/threshold-rules/",
        json={
            "equipment_type_id": equipment_type_id,
            "parameter_id": parameter_id,
            "warning_max": warning_max,
            "critical_max": critical_max,
            "is_active": True,
        },
    )
    assert response.status_code == 201


async def _create_equipment(client, equipment_type_id: str):
    response = await client.post(
        "/api/v1/equipment/",
        json={
            "name": f"Оборудование событий {uuid4().hex[:6]}",
            "code": f"EV-{uuid4().hex[:8]}",
            "serial_number": f"ES-{uuid4().hex[:8]}",
            "equipment_type_id": equipment_type_id,
            "location": "Карьер Stage 7",
            "description": "Оборудование для проверки event pipeline.",
            "specifications": {"power_kw": 200},
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _create_reading(client, equipment_id: str, parameter_id: str, value: str, minutes_ago: int):
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


async def test_events_are_created_for_warning_transition(client, set_current_user):
    await set_current_user(
        {
            "equipment.read",
            "equipment.manage",
            "telemetry.create",
            "telemetry.read",
            "threshold_rules.manage",
            "threshold_rules.read",
            "events.read",
        }
    )

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, "event_warning", "Температура ротора")
    await _create_binding(client, equipment_type_id, parameter_id)
    await _create_threshold_rule(client, equipment_type_id, parameter_id, warning_max="80.0", critical_max="95.0")
    equipment_id = await _create_equipment(client, equipment_type_id)

    await _create_reading(client, equipment_id, parameter_id, "85.0", 1)

    response = await client.get(f"/api/v1/events/?equipment_id={equipment_id}")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert {item["event_type"] for item in payload} == {"parameter_warning", "equipment_warning"}


async def test_events_are_created_for_recovery_transition(client, set_current_user):
    await set_current_user(
        {
            "equipment.read",
            "equipment.manage",
            "telemetry.create",
            "telemetry.read",
            "threshold_rules.manage",
            "threshold_rules.read",
            "events.read",
        }
    )

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, "event_recovery", "Температура масла")
    await _create_binding(client, equipment_type_id, parameter_id)
    await _create_threshold_rule(client, equipment_type_id, parameter_id, warning_max="80.0", critical_max="95.0")
    equipment_id = await _create_equipment(client, equipment_type_id)

    await _create_reading(client, equipment_id, parameter_id, "82.0", 2)
    await _create_reading(client, equipment_id, parameter_id, "70.0", 1)

    response = await client.get(f"/api/v1/events/?equipment_id={equipment_id}")
    assert response.status_code == 200
    payload = response.json()
    assert {item["event_type"] for item in payload} == {
        "parameter_warning",
        "equipment_warning",
        "parameter_recovered",
        "equipment_recovered",
    }


async def test_events_are_created_for_critical_to_warning_transition(client, set_current_user):
    await set_current_user(
        {
            "equipment.read",
            "equipment.manage",
            "telemetry.create",
            "telemetry.read",
            "threshold_rules.manage",
            "threshold_rules.read",
            "events.read",
        }
    )

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, "event_downgrade", "Температура картера")
    await _create_binding(client, equipment_type_id, parameter_id)
    await _create_threshold_rule(client, equipment_type_id, parameter_id, warning_max="80.0", critical_max="95.0")
    equipment_id = await _create_equipment(client, equipment_type_id)

    await _create_reading(client, equipment_id, parameter_id, "98.0", 2)
    await _create_reading(client, equipment_id, parameter_id, "85.0", 1)

    response = await client.get(f"/api/v1/events/?equipment_id={equipment_id}")
    assert response.status_code == 200
    payload = response.json()
    assert {item["event_type"] for item in payload} == {
        "parameter_critical",
        "equipment_critical",
        "parameter_warning",
        "equipment_warning",
    }


async def test_event_list_filters_by_event_type(client, set_current_user):
    await set_current_user(
        {
            "equipment.read",
            "equipment.manage",
            "telemetry.create",
            "telemetry.read",
            "threshold_rules.manage",
            "threshold_rules.read",
            "events.read",
        }
    )

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, "event_filter", "Вибрация редуктора")
    await _create_binding(client, equipment_type_id, parameter_id)
    await _create_threshold_rule(client, equipment_type_id, parameter_id, warning_max="7.5", critical_max="12.0")
    equipment_id = await _create_equipment(client, equipment_type_id)

    await _create_reading(client, equipment_id, parameter_id, "13.0", 1)

    response = await client.get(f"/api/v1/events/?equipment_id={equipment_id}&event_type=parameter_critical")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["event_type"] == "parameter_critical"
    assert payload[0]["severity"] == "critical"


async def test_event_list_filters_by_severity(client, set_current_user):
    await set_current_user(
        {
            "equipment.read",
            "equipment.manage",
            "telemetry.create",
            "telemetry.read",
            "threshold_rules.manage",
            "threshold_rules.read",
            "events.read",
        }
    )

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, "event_severity", "Температура привода")
    await _create_binding(client, equipment_type_id, parameter_id)
    await _create_threshold_rule(client, equipment_type_id, parameter_id, warning_max="80.0", critical_max="95.0")
    equipment_id = await _create_equipment(client, equipment_type_id)

    await _create_reading(client, equipment_id, parameter_id, "99.0", 1)

    response = await client.get(f"/api/v1/events/?equipment_id={equipment_id}&severity=critical")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert all(item["severity"] == "critical" for item in payload)


async def test_get_event_returns_existing_event(client, set_current_user):
    await set_current_user(
        {
            "equipment.read",
            "equipment.manage",
            "telemetry.create",
            "telemetry.read",
            "threshold_rules.manage",
            "threshold_rules.read",
            "events.read",
        }
    )

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, "event_get", "Температура редуктора")
    await _create_binding(client, equipment_type_id, parameter_id)
    await _create_threshold_rule(client, equipment_type_id, parameter_id, warning_max="80.0", critical_max="95.0")
    equipment_id = await _create_equipment(client, equipment_type_id)

    await _create_reading(client, equipment_id, parameter_id, "85.0", 1)

    list_response = await client.get(f"/api/v1/events/?equipment_id={equipment_id}&event_type=parameter_warning")
    assert list_response.status_code == 200
    event_id = list_response.json()[0]["id"]

    response = await client.get(f"/api/v1/events/{event_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == event_id
    assert payload["event_type"] == "parameter_warning"
    assert payload["equipment"]["id"] == equipment_id


async def test_event_list_requires_permission(client, set_current_user):
    await set_current_user(set())

    response = await client.get("/api/v1/events/")

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing permissions: events.read."


async def test_get_event_requires_permission(client, set_current_user):
    await set_current_user(set())

    response = await client.get(f"/api/v1/events/{uuid4()}")

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing permissions: events.read."


async def test_get_event_returns_404_for_unknown_id(client, set_current_user):
    await set_current_user({"events.read"})

    response = await client.get(f"/api/v1/events/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found."


async def test_event_list_rejects_unknown_event_type(client, set_current_user):
    await set_current_user({"events.read"})

    response = await client.get("/api/v1/events/?event_type=maintenance_needed")

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported event type filter."


async def test_event_list_rejects_unknown_severity(client, set_current_user):
    await set_current_user({"events.read"})

    response = await client.get("/api/v1/events/?severity=emergency")

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported event severity filter."


async def test_events_are_not_duplicated_when_status_does_not_change(client, set_current_user):
    await set_current_user(
        {
            "equipment.read",
            "equipment.manage",
            "telemetry.create",
            "telemetry.read",
            "threshold_rules.manage",
            "threshold_rules.read",
            "events.read",
        }
    )

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, "event_stable", "Температура статора")
    await _create_binding(client, equipment_type_id, parameter_id)
    await _create_threshold_rule(client, equipment_type_id, parameter_id, warning_max="80.0", critical_max="95.0")
    equipment_id = await _create_equipment(client, equipment_type_id)

    await _create_reading(client, equipment_id, parameter_id, "85.0", 2)
    await _create_reading(client, equipment_id, parameter_id, "86.0", 1)

    response = await client.get(f"/api/v1/events/?equipment_id={equipment_id}")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert {item["event_type"] for item in payload} == {"parameter_warning", "equipment_warning"}
