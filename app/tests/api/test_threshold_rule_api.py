from decimal import Decimal
from uuid import uuid4

import pytest


pytestmark = pytest.mark.asyncio


async def _create_equipment_type(client):
    response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Тип порогов {uuid4().hex[:8]}",
            "description": "Тип оборудования для тестирования пороговых правил.",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _create_parameter(client, code_prefix: str = "threshold"):
    response = await client.post(
        "/api/v1/parameters/",
        json={
            "code": f"{code_prefix}_{uuid4().hex[:8]}",
            "name": "Температура подшипника",
            "unit": "C",
            "description": "Параметр для тестирования пороговых правил.",
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
    return response.json()["id"]


async def _create_threshold_rule(client, equipment_type_id: str, parameter_id: str):
    response = await client.post(
        "/api/v1/threshold-rules/",
        json={
            "equipment_type_id": equipment_type_id,
            "parameter_id": parameter_id,
            "warning_min": "40.0",
            "warning_max": "80.0",
            "critical_min": "20.0",
            "critical_max": "95.0",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()


async def test_threshold_rule_crud_flow(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "threshold_rules.read", "threshold_rules.manage"})

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client)
    await _create_binding(client, equipment_type_id, parameter_id)

    create_response = await client.post(
        "/api/v1/threshold-rules/",
        json={
            "equipment_type_id": equipment_type_id,
            "parameter_id": parameter_id,
            "warning_min": "50.0",
            "warning_max": "75.0",
            "critical_min": "30.0",
            "critical_max": "90.0",
            "is_active": True,
        },
    )

    assert create_response.status_code == 201
    created_rule = create_response.json()
    rule_id = created_rule["id"]
    assert Decimal(str(created_rule["warning_min"])) == Decimal("50.0")
    assert Decimal(str(created_rule["critical_max"])) == Decimal("90.0")

    list_response = await client.get("/api/v1/threshold-rules/")
    assert list_response.status_code == 200
    assert any(item["id"] == rule_id for item in list_response.json())

    get_response = await client.get(f"/api/v1/threshold-rules/{rule_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == rule_id

    update_response = await client.patch(
        f"/api/v1/threshold-rules/{rule_id}",
        json={
            "warning_max": "78.5",
            "critical_max": "98.0",
            "is_active": False,
        },
    )
    assert update_response.status_code == 200
    updated_rule = update_response.json()
    assert Decimal(str(updated_rule["warning_max"])) == Decimal("78.5")
    assert Decimal(str(updated_rule["critical_max"])) == Decimal("98.0")
    assert updated_rule["is_active"] is False

    delete_response = await client.delete(f"/api/v1/threshold-rules/{rule_id}")
    assert delete_response.status_code == 204

    get_deleted_response = await client.get(f"/api/v1/threshold-rules/{rule_id}")
    assert get_deleted_response.status_code == 404


async def test_threshold_rule_create_requires_manage_permission(client, set_current_user):
    await set_current_user({"threshold_rules.read"})

    response = await client.post(
        "/api/v1/threshold-rules/",
        json={
            "equipment_type_id": str(uuid4()),
            "parameter_id": str(uuid4()),
            "warning_max": "70.0",
            "is_active": True,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing permissions: threshold_rules.manage."


async def test_threshold_rule_list_requires_read_permission(client, set_current_user):
    await set_current_user(set())

    response = await client.get("/api/v1/threshold-rules/")

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing permissions: threshold_rules.read."


async def test_threshold_rule_rejects_duplicate_rule(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "threshold_rules.manage"})

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, code_prefix="duplicate_rule")
    await _create_binding(client, equipment_type_id, parameter_id)

    first_response = await client.post(
        "/api/v1/threshold-rules/",
        json={
            "equipment_type_id": equipment_type_id,
            "parameter_id": parameter_id,
            "warning_max": "70.0",
            "is_active": True,
        },
    )
    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/threshold-rules/",
        json={
            "equipment_type_id": equipment_type_id,
            "parameter_id": parameter_id,
            "warning_min": "35.0",
            "is_active": True,
        },
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Threshold rule for this equipment type and parameter already exists."


async def test_threshold_rule_requires_existing_equipment_type_parameter_binding(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "threshold_rules.manage"})

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, code_prefix="binding_required")

    response = await client.post(
        "/api/v1/threshold-rules/",
        json={
            "equipment_type_id": equipment_type_id,
            "parameter_id": parameter_id,
            "warning_max": "80.0",
            "is_active": True,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Threshold rule requires an existing equipment type parameter binding."


async def test_threshold_rule_requires_at_least_one_threshold_value(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "threshold_rules.manage"})

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, code_prefix="no_values")
    await _create_binding(client, equipment_type_id, parameter_id)

    response = await client.post(
        "/api/v1/threshold-rules/",
        json={
            "equipment_type_id": equipment_type_id,
            "parameter_id": parameter_id,
            "is_active": True,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "At least one threshold value must be provided."


async def test_threshold_rule_validates_threshold_order(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "threshold_rules.manage"})

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, code_prefix="invalid_order")
    await _create_binding(client, equipment_type_id, parameter_id)

    response = await client.post(
        "/api/v1/threshold-rules/",
        json={
            "equipment_type_id": equipment_type_id,
            "parameter_id": parameter_id,
            "warning_min": "60.0",
            "critical_min": "65.0",
            "is_active": True,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "critical_min must be less than or equal to warning_min."


async def test_threshold_rule_update_validates_final_state(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "threshold_rules.read", "threshold_rules.manage"})

    equipment_type_id = await _create_equipment_type(client)
    parameter_id = await _create_parameter(client, code_prefix="update_final_state")
    await _create_binding(client, equipment_type_id, parameter_id)
    created_rule = await _create_threshold_rule(client, equipment_type_id, parameter_id)

    response = await client.patch(
        f"/api/v1/threshold-rules/{created_rule['id']}",
        json={
            "warning_min": None,
            "warning_max": None,
            "critical_min": None,
            "critical_max": None,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "At least one threshold value must be provided."


async def test_threshold_rule_update_rejects_duplicate_pair(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "threshold_rules.manage"})

    equipment_type_id = await _create_equipment_type(client)

    first_parameter_id = await _create_parameter(client, code_prefix="duplicate_pair_one")
    second_parameter_id = await _create_parameter(client, code_prefix="duplicate_pair_two")
    await _create_binding(client, equipment_type_id, first_parameter_id)
    await _create_binding(client, equipment_type_id, second_parameter_id)

    first_rule = await _create_threshold_rule(client, equipment_type_id, first_parameter_id)
    second_rule = await _create_threshold_rule(client, equipment_type_id, second_parameter_id)

    response = await client.patch(
        f"/api/v1/threshold-rules/{second_rule['id']}",
        json={"parameter_id": first_parameter_id},
    )

    assert first_rule["id"] != second_rule["id"]
    assert response.status_code == 400
    assert response.json()["detail"] == "Threshold rule for this equipment type and parameter already exists."


async def test_threshold_rule_list_filters_by_parameter_id(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "threshold_rules.read", "threshold_rules.manage"})

    first_type_id = await _create_equipment_type(client)
    second_type_id = await _create_equipment_type(client)
    target_parameter_id = await _create_parameter(client, code_prefix="filter_target")
    extra_parameter_id = await _create_parameter(client, code_prefix="filter_extra")

    await _create_binding(client, first_type_id, target_parameter_id)
    await _create_binding(client, second_type_id, target_parameter_id)
    await _create_binding(client, second_type_id, extra_parameter_id)

    await _create_threshold_rule(client, first_type_id, target_parameter_id)
    await _create_threshold_rule(client, second_type_id, target_parameter_id)
    await _create_threshold_rule(client, second_type_id, extra_parameter_id)

    response = await client.get(f"/api/v1/threshold-rules/?parameter_id={target_parameter_id}")

    assert response.status_code == 200
    rules = response.json()
    assert len(rules) == 2
    assert {item["equipment_type"]["id"] for item in rules} == {first_type_id, second_type_id}
    assert all(item["parameter"]["id"] == target_parameter_id for item in rules)


async def test_get_threshold_rule_returns_404_for_unknown_id(client, set_current_user):
    await set_current_user({"threshold_rules.read"})

    response = await client.get(f"/api/v1/threshold-rules/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Threshold rule not found."


async def test_update_threshold_rule_returns_404_for_unknown_id(client, set_current_user):
    await set_current_user({"threshold_rules.manage"})

    response = await client.patch(
        f"/api/v1/threshold-rules/{uuid4()}",
        json={"warning_max": "85.0"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Threshold rule not found."


async def test_delete_threshold_rule_returns_404_for_unknown_id(client, set_current_user):
    await set_current_user({"threshold_rules.manage"})

    response = await client.delete(f"/api/v1/threshold-rules/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Threshold rule not found."
