from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest


pytestmark = pytest.mark.asyncio


async def _create_equipment_type(client):
    response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Тип телеметрии {uuid4().hex[:8]}",
            "description": "Тип оборудования для телеметрии.",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _create_parameter(client, code_prefix: str = "telemetry"):
    response = await client.post(
        "/api/v1/parameters/",
        json={
            "code": f"{code_prefix}_{uuid4().hex[:8]}",
            "name": "Температура двигателя",
            "unit": "C",
            "description": "Параметр для тестирования телеметрии.",
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
    warning_max: str | None = "80.0",
    critical_min: str | None = None,
    critical_max: str | None = "95.0",
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
    return response.json()["id"]


async def _create_equipment(client, equipment_type_id: str, code_prefix: str = "TEL"):
    response = await client.post(
        "/api/v1/equipment/",
        json={
            "name": f"Единица телеметрии {uuid4().hex[:6]}",
            "code": f"{code_prefix}-{uuid4().hex[:8]}",
            "serial_number": f"SN-{uuid4().hex[:8]}",
            "equipment_type_id": equipment_type_id,
            "location": "Карьер 1",
            "description": "Оборудование для телеметрии.",
            "specifications": {"power_kw": 120},
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def test_telemetry_reading_flow(client, set_current_user):
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
    parameter_id = await _create_parameter(client)
    await _create_binding(client, equipment_type_id, parameter_id)
    await _create_threshold_rule(client, equipment_type_id, parameter_id)
    equipment_id = await _create_equipment(client, equipment_type_id)
    measured_at = datetime.now(UTC) - timedelta(minutes=2)

    create_response = await client.post(
        "/api/v1/telemetry-readings/",
        json={
            "equipment_id": equipment_id,
            "parameter_id": parameter_id,
            "value": "76.2500",
            "measured_at": measured_at.isoformat(),
        },
    )

    assert create_response.status_code == 201
    created_reading = create_response.json()
    reading_id = created_reading["id"]
    assert created_reading["equipment"]["id"] == equipment_id
    assert created_reading["parameter"]["id"] == parameter_id
    assert Decimal(str(created_reading["value"])) == Decimal("76.2500")
    assert created_reading["evaluation"]["status"] == "normal"

    list_response = await client.get(f"/api/v1/telemetry-readings/?equipment_id={equipment_id}")
    assert list_response.status_code == 200
    assert any(item["id"] == reading_id for item in list_response.json())

    get_response = await client.get(f"/api/v1/telemetry-readings/{reading_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == reading_id


async def test_telemetry_reading_create_requires_permission(client, set_current_user):
    await set_current_user({"telemetry.read"})

    response = await client.post(
        "/api/v1/telemetry-readings/",
        json={
            "equipment_id": str(uuid4()),
            "parameter_id": str(uuid4()),
            "value": "42.0",
            "measured_at": datetime.now(UTC).isoformat(),
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing permissions: telemetry.create."


async def test_telemetry_reading_list_requires_permission(client, set_current_user):
    await set_current_user(set())

    response = await client.get("/api/v1/telemetry-readings/")

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing permissions: telemetry.read."


async def test_telemetry_reading_create_rejects_unknown_equipment(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "telemetry.create"})

    parameter_id = await _create_parameter(client, code_prefix="unknown_equipment")

    response = await client.post(
        "/api/v1/telemetry-readings/",
        json={
            "equipment_id": str(uuid4()),
            "parameter_id": parameter_id,
            "value": "55.0",
            "measured_at": datetime.now(UTC).isoformat(),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Equipment was not found."


async def test_telemetry_reading_create_rejects_unknown_parameter(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "telemetry.create"})

    equipment_type_id = await _create_equipment_type(client)
    equipment_id = await _create_equipment(client, equipment_type_id)

    response = await client.post(
        "/api/v1/telemetry-readings/",
        json={
            "equipment_id": equipment_id,
            "parameter_id": str(uuid4()),
            "value": "55.0",
            "measured_at": datetime.now(UTC).isoformat(),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Parameter was not found."


async def test_telemetry_reading_create_rejects_unbound_parameter(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "telemetry.create"})

    equipment_type_id = await _create_equipment_type(client)
    bound_parameter_id = await _create_parameter(client, code_prefix="bound")
    unbound_parameter_id = await _create_parameter(client, code_prefix="unbound")
    await _create_binding(client, equipment_type_id, bound_parameter_id)
    equipment_id = await _create_equipment(client, equipment_type_id)

    response = await client.post(
        "/api/v1/telemetry-readings/",
        json={
            "equipment_id": equipment_id,
            "parameter_id": unbound_parameter_id,
            "value": "55.0",
            "measured_at": datetime.now(UTC).isoformat(),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Parameter is not assigned to the equipment type of the target equipment."


async def test_telemetry_reading_list_filters_by_equipment_id(client, set_current_user):
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
    parameter_id = await _create_parameter(client, code_prefix="filter")
    await _create_binding(client, equipment_type_id, parameter_id)
    await _create_threshold_rule(client, equipment_type_id, parameter_id)

    first_equipment_id = await _create_equipment(client, equipment_type_id, code_prefix="FLT1")
    second_equipment_id = await _create_equipment(client, equipment_type_id, code_prefix="FLT2")

    first_response = await client.post(
        "/api/v1/telemetry-readings/",
        json={
            "equipment_id": first_equipment_id,
            "parameter_id": parameter_id,
            "value": "60.0",
            "measured_at": (datetime.now(UTC) - timedelta(minutes=3)).isoformat(),
        },
    )
    second_response = await client.post(
        "/api/v1/telemetry-readings/",
        json={
            "equipment_id": second_equipment_id,
            "parameter_id": parameter_id,
            "value": "61.0",
            "measured_at": (datetime.now(UTC) - timedelta(minutes=2)).isoformat(),
        },
    )
    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = await client.get(f"/api/v1/telemetry-readings/?equipment_id={first_equipment_id}")

    assert response.status_code == 200
    readings = response.json()
    assert len(readings) == 1
    assert readings[0]["equipment"]["id"] == first_equipment_id


async def test_telemetry_reading_list_rejects_invalid_date_range(client, set_current_user):
    await set_current_user({"telemetry.read"})

    date_from = datetime.now(UTC)
    date_to = date_from - timedelta(hours=1)

    response = await client.get(
        "/api/v1/telemetry-readings/",
        params={
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "date_from must be less than or equal to date_to."


async def test_telemetry_reading_create_rejects_far_future_timestamp(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "telemetry.create"})

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, code_prefix="future")
    await _create_binding(client, equipment_type_id, parameter_id)
    equipment_id = await _create_equipment(client, equipment_type_id)

    response = await client.post(
        "/api/v1/telemetry-readings/",
        json={
            "equipment_id": equipment_id,
            "parameter_id": parameter_id,
            "value": "55.0",
            "measured_at": (datetime.now(UTC) + timedelta(minutes=10)).isoformat(),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "measured_at cannot be more than 5 minutes in the future."


async def test_get_telemetry_reading_returns_404_for_unknown_id(client, set_current_user):
    await set_current_user({"telemetry.read"})

    response = await client.get(f"/api/v1/telemetry-readings/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Telemetry reading not found."


async def test_telemetry_reading_create_rejects_missing_active_threshold_rule(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "telemetry.create"})

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, code_prefix="missing_rule")
    await _create_binding(client, equipment_type_id, parameter_id)
    equipment_id = await _create_equipment(client, equipment_type_id)

    response = await client.post(
        "/api/v1/telemetry-readings/",
        json={
            "equipment_id": equipment_id,
            "parameter_id": parameter_id,
            "value": "55.0",
            "measured_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Active threshold rule was not found for the equipment parameter pair."


async def test_telemetry_reading_create_rejects_naive_timestamp(client, set_current_user):
    await set_current_user(
        {
            "equipment.read",
            "equipment.manage",
            "telemetry.create",
            "threshold_rules.read",
            "threshold_rules.manage",
        }
    )

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, code_prefix="naive_time")
    await _create_binding(client, equipment_type_id, parameter_id)
    await _create_threshold_rule(client, equipment_type_id, parameter_id)
    equipment_id = await _create_equipment(client, equipment_type_id)

    response = await client.post(
        "/api/v1/telemetry-readings/",
        json={
            "equipment_id": equipment_id,
            "parameter_id": parameter_id,
            "value": "55.0",
            "measured_at": datetime.now().replace(microsecond=0).isoformat(),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "measured_at must include timezone information."


async def test_telemetry_reading_create_rejects_inactive_threshold_rule(client, set_current_user):
    await set_current_user(
        {
            "equipment.read",
            "equipment.manage",
            "telemetry.create",
            "threshold_rules.manage",
            "threshold_rules.read",
        }
    )

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, code_prefix="inactive_rule")
    await _create_binding(client, equipment_type_id, parameter_id)
    rule_id = await _create_threshold_rule(client, equipment_type_id, parameter_id)
    equipment_id = await _create_equipment(client, equipment_type_id)

    deactivate_response = await client.patch(
        f"/api/v1/threshold-rules/{rule_id}",
        json={"is_active": False},
    )
    assert deactivate_response.status_code == 200

    response = await client.post(
        "/api/v1/telemetry-readings/",
        json={
            "equipment_id": equipment_id,
            "parameter_id": parameter_id,
            "value": "55.0",
            "measured_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Active threshold rule was not found for the equipment parameter pair."
