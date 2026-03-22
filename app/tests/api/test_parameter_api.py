from uuid import uuid4

import pytest


pytestmark = pytest.mark.asyncio


async def test_parameter_crud_flow(client, set_current_user):
    set_current_user({"equipment.read", "equipment.manage"})

    create_response = await client.post(
        "/api/v1/parameters/",
        json={
            "code": f"temperature_{uuid4().hex[:8]}",
            "name": "Temperature",
            "unit": "C",
            "description": "Bearing temperature",
            "is_active": True,
        },
    )

    assert create_response.status_code == 201
    created_parameter = create_response.json()
    parameter_id = created_parameter["id"]
    assert created_parameter["name"] == "Temperature"

    list_response = await client.get("/api/v1/parameters/")
    assert list_response.status_code == 200
    assert any(item["id"] == parameter_id for item in list_response.json())

    get_response = await client.get(f"/api/v1/parameters/{parameter_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == parameter_id

    update_response = await client.patch(
        f"/api/v1/parameters/{parameter_id}",
        json={
            "name": "Updated Temperature",
            "unit": "degC",
            "description": "Updated description",
            "is_active": False,
        },
    )
    assert update_response.status_code == 200
    updated_parameter = update_response.json()
    assert updated_parameter["name"] == "Updated Temperature"
    assert updated_parameter["unit"] == "degC"
    assert updated_parameter["is_active"] is False
    delete_response = await client.delete(f"/api/v1/parameters/{parameter_id}")
    assert delete_response.status_code == 204

    get_deleted_response = await client.get(f"/api/v1/parameters/{parameter_id}")
    assert get_deleted_response.status_code == 404


async def test_parameter_create_requires_manage_permission(client, set_current_user):
    set_current_user({"equipment.read"})

    response = await client.post(
        "/api/v1/parameters/",
        json={
            "code": f"pressure_{uuid4().hex[:8]}",
            "name": "Pressure",
            "unit": "bar",
            "description": "Should be denied",
            "is_active": True,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing permissions: equipment.manage."


async def test_parameter_list_requires_read_permission(client, set_current_user):
    set_current_user(set())

    response = await client.get("/api/v1/parameters/")

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing permissions: equipment.read."


async def test_parameter_duplicate_code_returns_400(client, set_current_user):
    set_current_user({"equipment.read", "equipment.manage"})
    code = f"vibration_{uuid4().hex[:8]}"

    first_response = await client.post(
        "/api/v1/parameters/",
        json={
            "code": code,
            "name": "Vibration",
            "unit": "mm/s",
            "description": "First parameter",
            "is_active": True,
        },
    )
    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/parameters/",
        json={
            "code": code,
            "name": "Vibration Copy",
            "unit": "mm/s",
            "description": "Second parameter",
            "is_active": True,
        },
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == f"Parameter with code '{code}' already exists."


async def test_get_parameter_returns_404_for_unknown_id(client, set_current_user):
    set_current_user({"equipment.read"})

    response = await client.get(f"/api/v1/parameters/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Parameter not found."


async def test_update_parameter_returns_404_for_unknown_id(client, set_current_user):
    set_current_user({"equipment.manage"})

    response = await client.patch(
        f"/api/v1/parameters/{uuid4()}",
        json={"name": "Не найденный параметр"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Parameter not found."


async def test_delete_parameter_returns_404_for_unknown_id(client, set_current_user):
    set_current_user({"equipment.manage"})

    response = await client.delete(f"/api/v1/parameters/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Parameter not found."


async def test_equipment_type_parameter_binding_flow(client, set_current_user):
    set_current_user({"equipment.read", "equipment.manage"})

    type_response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Binding Type {uuid4().hex[:8]}",
            "description": "Binding test type",
            "is_active": True,
        },
    )
    assert type_response.status_code == 201
    equipment_type_id = type_response.json()["id"]

    parameter_response = await client.post(
        "/api/v1/parameters/",
        json={
            "code": f"load_{uuid4().hex[:8]}",
            "name": "Load",
            "unit": "%",
            "description": "Engine load",
            "is_active": True,
        },
    )
    assert parameter_response.status_code == 201
    parameter_id = parameter_response.json()["id"]

    create_response = await client.post(
        "/api/v1/equipment-type-parameters/",
        json={
            "equipment_type_id": equipment_type_id,
            "parameter_id": parameter_id,
            "is_required": True,
        },
    )
    assert create_response.status_code == 201
    created_binding = create_response.json()
    binding_id = created_binding["id"]
    assert created_binding["equipment_type"]["id"] == equipment_type_id
    assert created_binding["parameter"]["id"] == parameter_id
    assert created_binding["is_required"] is True

    list_response = await client.get(
        f"/api/v1/equipment-type-parameters/?equipment_type_id={equipment_type_id}"
    )
    assert list_response.status_code == 200
    assert any(item["id"] == binding_id for item in list_response.json())

    get_response = await client.get(f"/api/v1/equipment-type-parameters/{binding_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == binding_id

    delete_response = await client.delete(f"/api/v1/equipment-type-parameters/{binding_id}")
    assert delete_response.status_code == 204

    get_deleted_response = await client.get(f"/api/v1/equipment-type-parameters/{binding_id}")
    assert get_deleted_response.status_code == 404


async def test_equipment_type_parameter_duplicate_binding_returns_400(client, set_current_user):
    set_current_user({"equipment.read", "equipment.manage"})

    type_response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Duplicate Binding Type {uuid4().hex[:8]}",
            "description": "Duplicate binding type",
            "is_active": True,
        },
    )
    equipment_type_id = type_response.json()["id"]

    parameter_response = await client.post(
        "/api/v1/parameters/",
        json={
            "code": f"rpm_{uuid4().hex[:8]}",
            "name": "RPM",
            "unit": "rpm",
            "description": "Rotation speed",
            "is_active": True,
        },
    )
    parameter_id = parameter_response.json()["id"]

    first_response = await client.post(
        "/api/v1/equipment-type-parameters/",
        json={
            "equipment_type_id": equipment_type_id,
            "parameter_id": parameter_id,
            "is_required": True,
        },
    )
    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/equipment-type-parameters/",
        json={
            "equipment_type_id": equipment_type_id,
            "parameter_id": parameter_id,
            "is_required": False,
        },
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Parameter is already assigned to this equipment type."


async def test_equipment_type_parameter_create_requires_manage_permission(client, set_current_user):
    set_current_user({"equipment.read"})

    response = await client.post(
        "/api/v1/equipment-type-parameters/",
        json={
            "equipment_type_id": str(uuid4()),
            "parameter_id": str(uuid4()),
            "is_required": True,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing permissions: equipment.manage."


async def test_equipment_type_parameter_create_rejects_unknown_equipment_type(client, set_current_user):
    set_current_user({"equipment.read", "equipment.manage"})

    parameter_response = await client.post(
        "/api/v1/parameters/",
        json={
            "code": f"temp_unknown_type_{uuid4().hex[:8]}",
            "name": "Температура двигателя",
            "unit": "C",
            "description": "Параметр для проверки неизвестного типа.",
            "is_active": True,
        },
    )
    assert parameter_response.status_code == 201
    parameter_id = parameter_response.json()["id"]

    response = await client.post(
        "/api/v1/equipment-type-parameters/",
        json={
            "equipment_type_id": str(uuid4()),
            "parameter_id": parameter_id,
            "is_required": True,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Equipment type was not found."


async def test_equipment_type_parameter_create_rejects_unknown_parameter(client, set_current_user):
    set_current_user({"equipment.read", "equipment.manage"})

    type_response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Неизвестный параметр {uuid4().hex[:8]}",
            "description": "Тип для проверки отсутствующего параметра",
            "is_active": True,
        },
    )
    assert type_response.status_code == 201
    equipment_type_id = type_response.json()["id"]

    response = await client.post(
        "/api/v1/equipment-type-parameters/",
        json={
            "equipment_type_id": equipment_type_id,
            "parameter_id": str(uuid4()),
            "is_required": True,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Parameter was not found."


async def test_equipment_type_parameter_list_filters_by_parameter_id(client, set_current_user):
    set_current_user({"equipment.read", "equipment.manage"})

    first_type_response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Фильтр тип 1 {uuid4().hex[:8]}",
            "description": "Первый тип для фильтрации",
            "is_active": True,
        },
    )
    second_type_response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Фильтр тип 2 {uuid4().hex[:8]}",
            "description": "Второй тип для фильтрации",
            "is_active": True,
        },
    )
    assert first_type_response.status_code == 201
    assert second_type_response.status_code == 201

    parameter_response = await client.post(
        "/api/v1/parameters/",
        json={
            "code": f"filter_param_{uuid4().hex[:8]}",
            "name": "Фильтруемый параметр",
            "unit": "бар",
            "description": "Параметр для проверки фильтрации по identifier.",
            "is_active": True,
        },
    )
    second_parameter_response = await client.post(
        "/api/v1/parameters/",
        json={
            "code": f"filter_param_extra_{uuid4().hex[:8]}",
            "name": "Дополнительный параметр",
            "unit": "C",
            "description": "Параметр для исключения из результата.",
            "is_active": True,
        },
    )
    assert parameter_response.status_code == 201
    assert second_parameter_response.status_code == 201

    target_parameter_id = parameter_response.json()["id"]
    extra_parameter_id = second_parameter_response.json()["id"]
    first_type_id = first_type_response.json()["id"]
    second_type_id = second_type_response.json()["id"]

    first_binding_response = await client.post(
        "/api/v1/equipment-type-parameters/",
        json={
            "equipment_type_id": first_type_id,
            "parameter_id": target_parameter_id,
            "is_required": True,
        },
    )
    second_binding_response = await client.post(
        "/api/v1/equipment-type-parameters/",
        json={
            "equipment_type_id": second_type_id,
            "parameter_id": target_parameter_id,
            "is_required": False,
        },
    )
    extra_binding_response = await client.post(
        "/api/v1/equipment-type-parameters/",
        json={
            "equipment_type_id": second_type_id,
            "parameter_id": extra_parameter_id,
            "is_required": True,
        },
    )
    assert first_binding_response.status_code == 201
    assert second_binding_response.status_code == 201
    assert extra_binding_response.status_code == 201

    response = await client.get(f"/api/v1/equipment-type-parameters/?parameter_id={target_parameter_id}")

    assert response.status_code == 200
    bindings = response.json()
    assert len(bindings) == 2
    assert {item["equipment_type"]["id"] for item in bindings} == {first_type_id, second_type_id}
    assert all(item["parameter"]["id"] == target_parameter_id for item in bindings)


async def test_get_equipment_type_parameter_returns_404_for_unknown_id(client, set_current_user):
    set_current_user({"equipment.read"})

    response = await client.get(f"/api/v1/equipment-type-parameters/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Equipment type parameter binding not found."


async def test_delete_equipment_type_parameter_returns_404_for_unknown_id(client, set_current_user):
    set_current_user({"equipment.manage"})

    response = await client.delete(f"/api/v1/equipment-type-parameters/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Equipment type parameter binding not found."


async def test_equipment_type_parameter_list_requires_read_permission(client, set_current_user):
    set_current_user(set())

    response = await client.get("/api/v1/equipment-type-parameters/")

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing permissions: equipment.read."


async def test_parameter_delete_rejects_assigned_bindings(client, set_current_user):
    set_current_user({"equipment.read", "equipment.manage"})

    type_response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Protected Param Type {uuid4().hex[:8]}",
            "description": "Protected parameter type",
            "is_active": True,
        },
    )
    equipment_type_id = type_response.json()["id"]

    parameter_response = await client.post(
        "/api/v1/parameters/",
        json={
            "code": f"fuel_rate_{uuid4().hex[:8]}",
            "name": "Fuel Rate",
            "unit": "l/h",
            "description": "Fuel consumption",
            "is_active": True,
        },
    )
    parameter_id = parameter_response.json()["id"]

    binding_response = await client.post(
        "/api/v1/equipment-type-parameters/",
        json={
            "equipment_type_id": equipment_type_id,
            "parameter_id": parameter_id,
            "is_required": True,
        },
    )
    assert binding_response.status_code == 201

    delete_response = await client.delete(f"/api/v1/parameters/{parameter_id}")
    assert delete_response.status_code == 400
    assert delete_response.json()["detail"] == "Parameter cannot be deleted while assigned to equipment types."
