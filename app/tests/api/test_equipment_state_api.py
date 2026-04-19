from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest


pytestmark = pytest.mark.asyncio


async def _create_equipment_type(client):
    response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Тип состояния {uuid4().hex[:8]}",
            "description": "Тип оборудования для Stage 6.",
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
            "description": "Параметр для Stage 6.",
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
    warning_min: str | None = None,
    warning_max: str | None = None,
    critical_min: str | None = None,
    critical_max: str | None = None,
):
    payload = {
        "equipment_type_id": equipment_type_id,
        "parameter_id": parameter_id,
        "is_active": True,
    }
    if warning_min is not None:
        payload["warning_min"] = warning_min
    if warning_max is not None:
        payload["warning_max"] = warning_max
    if critical_min is not None:
        payload["critical_min"] = critical_min
    if critical_max is not None:
        payload["critical_max"] = critical_max

    response = await client.post("/api/v1/threshold-rules/", json=payload)
    assert response.status_code == 201


async def _create_equipment(client, equipment_type_id: str):
    response = await client.post(
        "/api/v1/equipment/",
        json={
            "name": f"Оборудование состояния {uuid4().hex[:6]}",
            "code": f"ST-{uuid4().hex[:8]}",
            "serial_number": f"SS-{uuid4().hex[:8]}",
            "equipment_type_id": equipment_type_id,
            "location": "Карьер Stage 6",
            "description": "Оборудование для проверки current state.",
            "specifications": {"power_kw": 180},
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


async def test_equipment_state_is_updated_from_new_telemetry(client, set_current_user):
    await set_current_user(
        {
            "equipment.read",
            "equipment.manage",
            "telemetry.read",
            "telemetry.create",
            "threshold_rules.read",
            "threshold_rules.manage",
        }
    )

    equipment_type_id = await _create_equipment_type(client)
    temperature_id = await _create_parameter(client, "state_temp", "Температура двигателя")
    vibration_id = await _create_parameter(client, "state_vibration", "Вибрация редуктора")
    await _create_binding(client, equipment_type_id, temperature_id)
    await _create_binding(client, equipment_type_id, vibration_id)
    await _create_threshold_rule(client, equipment_type_id, temperature_id, warning_max="80.0", critical_max="95.0")
    await _create_threshold_rule(client, equipment_type_id, vibration_id, warning_max="7.5", critical_max="12.0")
    equipment_id = await _create_equipment(client, equipment_type_id)

    first_reading = await _create_reading(client, equipment_id, temperature_id, "85.0", 3)
    assert first_reading["evaluation"]["status"] == "warning"

    state_response = await client.get(f"/api/v1/equipment-states/{equipment_id}")
    assert state_response.status_code == 200
    state_payload = state_response.json()
    assert state_payload["status"] == "warning"
    assert state_payload["warning_count"] == 1
    assert state_payload["critical_count"] == 0
    assert len(state_payload["parameter_states"]) == 1

    second_reading = await _create_reading(client, equipment_id, vibration_id, "13.0", 2)
    assert second_reading["evaluation"]["status"] == "critical"

    state_response = await client.get(f"/api/v1/equipment-states/{equipment_id}")
    updated_payload = state_response.json()
    assert updated_payload["status"] == "critical"
    assert updated_payload["warning_count"] == 1
    assert updated_payload["critical_count"] == 1
    assert len(updated_payload["parameter_states"]) == 2


async def test_equipment_state_can_recover_to_normal(client, set_current_user):
    await set_current_user(
        {
            "equipment.read",
            "equipment.manage",
            "telemetry.read",
            "telemetry.create",
            "threshold_rules.manage",
            "threshold_rules.read",
        }
    )

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, "recover_temp", "Температура масла")
    await _create_binding(client, equipment_type_id, parameter_id)
    await _create_threshold_rule(client, equipment_type_id, parameter_id, warning_max="80.0", critical_max="95.0")
    equipment_id = await _create_equipment(client, equipment_type_id)

    warning_reading = await _create_reading(client, equipment_id, parameter_id, "82.0", 2)
    assert warning_reading["evaluation"]["status"] == "warning"

    recovered_reading = await _create_reading(client, equipment_id, parameter_id, "70.0", 1)
    assert recovered_reading["evaluation"]["status"] == "normal"

    response = await client.get(f"/api/v1/equipment-states/{equipment_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "normal"
    assert payload["warning_count"] == 0
    assert payload["critical_count"] == 0
    assert len(payload["parameter_states"]) == 1
    assert payload["parameter_states"][0]["status"] == "normal"


async def test_equipment_state_list_filters_by_status(client, set_current_user):
    await set_current_user(
        {
            "equipment.read",
            "equipment.manage",
            "telemetry.read",
            "telemetry.create",
            "threshold_rules.manage",
            "threshold_rules.read",
        }
    )

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, "filter_state", "Температура подшипника")
    await _create_binding(client, equipment_type_id, parameter_id)
    await _create_threshold_rule(client, equipment_type_id, parameter_id, warning_max="80.0", critical_max="95.0")

    warning_equipment_id = await _create_equipment(client, equipment_type_id)
    normal_equipment_id = await _create_equipment(client, equipment_type_id)

    await _create_reading(client, warning_equipment_id, parameter_id, "88.0", 2)
    await _create_reading(client, normal_equipment_id, parameter_id, "70.0", 1)

    response = await client.get("/api/v1/equipment-states/?status=warning")
    assert response.status_code == 200
    payload = response.json()
    assert any(item["equipment"]["id"] == warning_equipment_id for item in payload)
    assert all(item["status"] == "warning" for item in payload)
    assert all(item["equipment"]["id"] != normal_equipment_id for item in payload)


async def test_equipment_state_list_requires_permission(client, set_current_user):
    await set_current_user(set())

    response = await client.get("/api/v1/equipment-states/")

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing permissions: equipment.read."


async def test_get_equipment_state_returns_404_for_unknown_equipment(client, set_current_user):
    await set_current_user({"equipment.read"})

    response = await client.get(f"/api/v1/equipment-states/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Equipment state not found."


async def test_equipment_state_list_rejects_unknown_status_filter(client, set_current_user):
    await set_current_user({"equipment.read"})

    response = await client.get("/api/v1/equipment-states/?status=offline")

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported equipment status filter."
