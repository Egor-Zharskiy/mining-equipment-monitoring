from uuid import uuid4

import pytest


pytestmark = pytest.mark.asyncio


async def test_equipment_type_crud_flow(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage"})

    create_response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Test Type {uuid4().hex[:8]}",
            "description": "Test equipment type",
            "is_active": True,
        },
    )

    assert create_response.status_code == 201
    created_type = create_response.json()
    equipment_type_id = created_type["id"]
    assert created_type["description"] == "Test equipment type"

    list_response = await client.get("/api/v1/equipment-types/")
    assert list_response.status_code == 200
    assert any(item["id"] == equipment_type_id for item in list_response.json())

    get_response = await client.get(f"/api/v1/equipment-types/{equipment_type_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == equipment_type_id

    update_response = await client.patch(
        f"/api/v1/equipment-types/{equipment_type_id}",
        json={"description": "Updated equipment type", "is_active": False},
    )
    assert update_response.status_code == 200
    updated_type = update_response.json()
    assert updated_type["description"] == "Updated equipment type"
    assert updated_type["is_active"] is False

    delete_response = await client.delete(f"/api/v1/equipment-types/{equipment_type_id}")
    assert delete_response.status_code == 204

    get_deleted_response = await client.get(f"/api/v1/equipment-types/{equipment_type_id}")
    assert get_deleted_response.status_code == 404


async def test_equipment_type_create_requires_manage_permission(client, set_current_user):
    await set_current_user({"equipment.read"})

    response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Denied Type {uuid4().hex[:8]}",
            "description": "Should be denied",
            "is_active": True,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing permissions: equipment.manage."


async def test_equipment_type_duplicate_name_returns_400(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage"})
    name = f"Duplicate Type {uuid4().hex[:8]}"

    first_response = await client.post(
        "/api/v1/equipment-types/",
        json={"name": name, "description": "First", "is_active": True},
    )
    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/equipment-types/",
        json={"name": name, "description": "Second", "is_active": True},
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == f"Equipment type with name '{name}' already exists."


async def test_equipment_type_delete_rejects_linked_equipment(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage"})

    type_response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Linked Type {uuid4().hex[:8]}",
            "description": "Used by equipment",
            "is_active": True,
        },
    )
    equipment_type_id = type_response.json()["id"]

    equipment_response = await client.post(
        "/api/v1/equipment/",
        json={
            "name": "Linked Equipment",
            "code": f"TEST-{uuid4().hex[:8]}",
            "serial_number": f"SER-{uuid4().hex[:8]}",
            "equipment_type_id": equipment_type_id,
            "location": "Test site",
            "description": "Linked equipment description",
            "specifications": {"power_kw": 100},
            "is_active": True,
        },
    )
    assert equipment_response.status_code == 201

    delete_response = await client.delete(f"/api/v1/equipment-types/{equipment_type_id}")
    assert delete_response.status_code == 400
    assert delete_response.json()["detail"] == "Equipment type cannot be deleted while assigned equipment exists."


async def test_equipment_crud_flow(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage"})

    type_response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Equipment Flow Type {uuid4().hex[:8]}",
            "description": "Equipment flow type",
            "is_active": True,
        },
    )
    equipment_type_id = type_response.json()["id"]

    create_response = await client.post(
        "/api/v1/equipment/",
        json={
            "name": "Test Equipment Unit",
            "code": f"EQ-{uuid4().hex[:8]}",
            "serial_number": f"SN-{uuid4().hex[:8]}",
            "equipment_type_id": equipment_type_id,
            "location": "West pit",
            "description": "Equipment under test",
            "specifications": {"capacity_tph": 420},
            "is_active": True,
        },
    )

    assert create_response.status_code == 201
    created_equipment = create_response.json()
    equipment_id = created_equipment["id"]
    assert created_equipment["equipment_type"]["id"] == equipment_type_id

    list_response = await client.get("/api/v1/equipment/")
    assert list_response.status_code == 200
    assert any(item["id"] == equipment_id for item in list_response.json())

    get_response = await client.get(f"/api/v1/equipment/{equipment_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == equipment_id

    update_response = await client.patch(
        f"/api/v1/equipment/{equipment_id}",
        json={
            "location": "Updated west pit",
            "description": "Updated equipment",
            "is_active": False,
            "specifications": {"capacity_tph": 500},
        },
    )
    assert update_response.status_code == 200
    updated_equipment = update_response.json()
    assert updated_equipment["location"] == "Updated west pit"
    assert updated_equipment["is_active"] is False
    assert updated_equipment["specifications"] == {"capacity_tph": 500}

    delete_response = await client.delete(f"/api/v1/equipment/{equipment_id}")
    assert delete_response.status_code == 204

    get_deleted_response = await client.get(f"/api/v1/equipment/{equipment_id}")
    assert get_deleted_response.status_code == 404


async def test_equipment_create_requires_manage_permission(client, set_current_user):
    await set_current_user({"equipment.read"})

    response = await client.post(
        "/api/v1/equipment/",
        json={
            "name": "Denied Equipment",
            "code": f"DEN-{uuid4().hex[:8]}",
            "serial_number": f"DNS-{uuid4().hex[:8]}",
            "equipment_type_id": str(uuid4()),
            "location": "Restricted area",
            "description": "Should be denied",
            "specifications": {"power_kw": 50},
            "is_active": True,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing permissions: equipment.manage."


async def test_equipment_create_with_unknown_type_returns_400(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage"})

    response = await client.post(
        "/api/v1/equipment/",
        json={
            "name": "Unknown Type Equipment",
            "code": f"UNK-{uuid4().hex[:8]}",
            "serial_number": f"UNS-{uuid4().hex[:8]}",
            "equipment_type_id": str(uuid4()),
            "location": "Unknown site",
            "description": "Missing type reference",
            "specifications": {"pressure_bar": 10},
            "is_active": True,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Equipment type was not found."


async def test_equipment_create_duplicate_code_returns_400(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage"})

    type_response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Duplicate Code Type {uuid4().hex[:8]}",
            "description": "Duplicate code type",
            "is_active": True,
        },
    )
    equipment_type_id = type_response.json()["id"]
    duplicate_code = f"DUP-{uuid4().hex[:8]}"

    first_response = await client.post(
        "/api/v1/equipment/",
        json={
            "name": "First Equipment",
            "code": duplicate_code,
            "serial_number": f"SER-{uuid4().hex[:8]}",
            "equipment_type_id": equipment_type_id,
            "location": "First site",
            "description": "First equipment",
            "specifications": {"load_tons": 25},
            "is_active": True,
        },
    )
    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/equipment/",
        json={
            "name": "Second Equipment",
            "code": duplicate_code,
            "serial_number": f"SER-{uuid4().hex[:8]}",
            "equipment_type_id": equipment_type_id,
            "location": "Second site",
            "description": "Second equipment",
            "specifications": {"load_tons": 30},
            "is_active": True,
        },
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == f"Equipment with code '{duplicate_code}' already exists."


async def test_equipment_type_update_can_clear_description(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage"})

    create_response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Clear Description Type {uuid4().hex[:8]}",
            "description": "Будет очищено",
            "is_active": True,
        },
    )
    equipment_type_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/equipment-types/{equipment_type_id}",
        json={"description": None},
    )

    assert update_response.status_code == 200
    assert update_response.json()["description"] is None


async def test_equipment_update_can_clear_nullable_fields(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage"})

    type_response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Clearable Equipment Type {uuid4().hex[:8]}",
            "description": "Тип для nullable полей",
            "is_active": True,
        },
    )
    equipment_type_id = type_response.json()["id"]

    create_response = await client.post(
        "/api/v1/equipment/",
        json={
            "name": "Clearable Equipment",
            "code": f"CLR-{uuid4().hex[:8]}",
            "serial_number": f"CLS-{uuid4().hex[:8]}",
            "equipment_type_id": equipment_type_id,
            "location": "North pit",
            "description": "Будет очищено",
            "specifications": {"power_kw": 220},
            "is_active": True,
        },
    )
    equipment_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/equipment/{equipment_id}",
        json={
            "serial_number": None,
            "description": None,
            "specifications": None,
        },
    )

    assert update_response.status_code == 200
    payload = update_response.json()
    assert payload["serial_number"] is None
    assert payload["description"] is None
    assert payload["specifications"] is None
