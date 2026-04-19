from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.models import User
from app.services.security_service import SecurityService


pytestmark = pytest.mark.asyncio


async def _create_user(db_session, *, email_prefix: str) -> User:
    user = User(
        username=f"user_{uuid4().hex[:8]}",
        email=f"{email_prefix}_{uuid4().hex[:8]}@example.com",
        hashed_password=SecurityService.hash_password("StrongPass123!"),
        first_name="Тех",
        last_name="Специалист",
        is_active=True,
        roles=[],
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


async def _create_equipment_type(client):
    response = await client.post(
        "/api/v1/equipment-types/",
        json={
            "name": f"Тип ТО {uuid4().hex[:8]}",
            "description": "Тип оборудования для maintenance stage.",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _create_equipment(client, equipment_type_id: str, *, code_prefix: str = "MNT"):
    response = await client.post(
        "/api/v1/equipment/",
        json={
            "name": f"Оборудование ТО {uuid4().hex[:6]}",
            "code": f"{code_prefix}-{uuid4().hex[:8]}",
            "serial_number": f"MS-{uuid4().hex[:8]}",
            "equipment_type_id": equipment_type_id,
            "location": "Ремзона",
            "description": "Оборудование для maintenance тестов.",
            "specifications": {"power_kw": 180},
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def test_maintenance_plan_crud_flow(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "maintenance.read", "maintenance.manage"})

    equipment_type_id = await _create_equipment_type(client)

    create_response = await client.post(
        "/api/v1/maintenance-plans/",
        json={
            "equipment_type_id": equipment_type_id,
            "title": "Плановое ТО каждые 30 дней",
            "description": "Проверка узлов и смазка.",
            "interval_days": 30,
            "is_active": True,
        },
    )
    assert create_response.status_code == 201
    plan_id = create_response.json()["id"]
    assert create_response.json()["equipment_type"]["id"] == equipment_type_id

    list_response = await client.get(f"/api/v1/maintenance-plans/?equipment_type_id={equipment_type_id}")
    assert list_response.status_code == 200
    assert any(item["id"] == plan_id for item in list_response.json())

    get_response = await client.get(f"/api/v1/maintenance-plans/{plan_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == plan_id

    update_response = await client.patch(
        f"/api/v1/maintenance-plans/{plan_id}",
        json={
            "description": None,
            "interval_days": 45,
            "is_active": False,
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["description"] is None
    assert updated["interval_days"] == 45
    assert updated["is_active"] is False

    delete_response = await client.delete(f"/api/v1/maintenance-plans/{plan_id}")
    assert delete_response.status_code == 204

    get_deleted_response = await client.get(f"/api/v1/maintenance-plans/{plan_id}")
    assert get_deleted_response.status_code == 404


async def test_maintenance_plan_create_requires_manage_permission(client, set_current_user):
    await set_current_user({"maintenance.read"})

    response = await client.post(
        "/api/v1/maintenance-plans/",
        json={
            "equipment_type_id": str(uuid4()),
            "title": "Недоступный план",
            "interval_days": 30,
            "is_active": True,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing permissions: maintenance.manage."


async def test_maintenance_plan_list_requires_read_permission(client, set_current_user):
    await set_current_user(set())

    response = await client.get("/api/v1/maintenance-plans/")

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing permissions: maintenance.read."


async def test_maintenance_plan_create_rejects_invalid_target_configuration(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "maintenance.manage"})

    response_without_target = await client.post(
        "/api/v1/maintenance-plans/",
        json={
            "title": "План без цели",
            "interval_days": 30,
            "is_active": True,
        },
    )
    assert response_without_target.status_code == 400
    assert (
        response_without_target.json()["detail"]
        == "Maintenance plan must target exactly one entity: equipment_type_id or equipment_id."
    )

    equipment_type_id = await _create_equipment_type(client)
    equipment_id = await _create_equipment(client, equipment_type_id)

    response_with_both_targets = await client.post(
        "/api/v1/maintenance-plans/",
        json={
            "equipment_type_id": equipment_type_id,
            "equipment_id": equipment_id,
            "title": "План с двумя целями",
            "interval_days": 30,
            "is_active": True,
        },
    )
    assert response_with_both_targets.status_code == 400
    assert (
        response_with_both_targets.json()["detail"]
        == "Maintenance plan must target exactly one entity: equipment_type_id or equipment_id."
    )


async def test_maintenance_plan_create_rejects_missing_interval(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "maintenance.manage"})

    equipment_type_id = await _create_equipment_type(client)
    response = await client.post(
        "/api/v1/maintenance-plans/",
        json={
            "equipment_type_id": equipment_type_id,
            "title": "План без интервала",
            "is_active": True,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Maintenance plan requires interval_hours or interval_days."


async def test_maintenance_task_flow_and_record_creation(client, db_session, set_current_user):
    actor = await _create_user(db_session, email_prefix="maintenance_actor")
    assignee = await _create_user(db_session, email_prefix="maintenance_assignee")
    await set_current_user(
        {"equipment.read", "equipment.manage", "maintenance.read", "maintenance.manage"},
        user_id=actor.id,
    )

    equipment_type_id = await _create_equipment_type(client)
    equipment_id = await _create_equipment(client, equipment_type_id)

    plan_response = await client.post(
        "/api/v1/maintenance-plans/",
        json={
            "equipment_type_id": equipment_type_id,
            "title": "Плановое обслуживание редуктора",
            "description": "Замена масла и проверка люфтов.",
            "interval_days": 60,
            "is_active": True,
        },
    )
    assert plan_response.status_code == 201
    plan_id = plan_response.json()["id"]

    create_task_response = await client.post(
        "/api/v1/maintenance-tasks/",
        json={
            "plan_id": plan_id,
            "equipment_id": equipment_id,
            "priority": "high",
            "due_at": (datetime.now(UTC) + timedelta(days=2)).isoformat(),
            "assigned_to_user_id": str(assignee.id),
        },
    )
    assert create_task_response.status_code == 201
    created_task = create_task_response.json()
    task_id = created_task["id"]
    assert created_task["status"] == "open"
    assert created_task["title"] == "Плановое обслуживание редуктора"
    assert created_task["created_by_user"]["id"] == str(actor.id)
    assert created_task["assigned_to_user"]["id"] == str(assignee.id)

    update_task_response = await client.patch(
        f"/api/v1/maintenance-tasks/{task_id}",
        json={
            "status": "in_progress",
            "due_at": None,
        },
    )
    assert update_task_response.status_code == 200
    updated_task = update_task_response.json()
    assert updated_task["status"] == "in_progress"
    assert updated_task["due_at"] is None

    complete_response = await client.post(
        f"/api/v1/maintenance-tasks/{task_id}/complete",
        json={
            "summary": "Работы выполнены",
            "details": "Заменено масло, проведен осмотр.",
            "performed_at": datetime.now(UTC).isoformat(),
        },
    )
    assert complete_response.status_code == 201
    created_record = complete_response.json()
    record_id = created_record["id"]
    assert created_record["task"]["id"] == task_id
    assert created_record["task"]["status"] == "done"
    assert created_record["performed_by_user"]["id"] == str(actor.id)

    task_response = await client.get(f"/api/v1/maintenance-tasks/{task_id}")
    assert task_response.status_code == 200
    assert task_response.json()["status"] == "done"
    assert task_response.json()["completed_at"] is not None

    records_response = await client.get(f"/api/v1/maintenance-records/?task_id={task_id}")
    assert records_response.status_code == 200
    assert len(records_response.json()) == 1
    assert records_response.json()[0]["id"] == record_id

    record_response = await client.get(f"/api/v1/maintenance-records/{record_id}")
    assert record_response.status_code == 200
    assert record_response.json()["id"] == record_id


async def test_maintenance_task_create_requires_manage_permission(client, set_current_user):
    await set_current_user({"maintenance.read"})

    response = await client.post(
        "/api/v1/maintenance-tasks/",
        json={
            "equipment_id": str(uuid4()),
            "title": "Недоступная задача",
            "priority": "medium",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing permissions: maintenance.manage."


async def test_maintenance_task_and_record_lists_require_read_permission(client, set_current_user):
    await set_current_user(set())

    tasks_response = await client.get("/api/v1/maintenance-tasks/")
    assert tasks_response.status_code == 403
    assert tasks_response.json()["detail"] == "Missing permissions: maintenance.read."

    records_response = await client.get("/api/v1/maintenance-records/")
    assert records_response.status_code == 403
    assert records_response.json()["detail"] == "Missing permissions: maintenance.read."


async def test_maintenance_task_create_rejects_incompatible_plan(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "maintenance.manage"})

    first_type_id = await _create_equipment_type(client)
    second_type_id = await _create_equipment_type(client)
    equipment_id = await _create_equipment(client, second_type_id)

    plan_response = await client.post(
        "/api/v1/maintenance-plans/",
        json={
            "equipment_type_id": first_type_id,
            "title": "План для другого типа",
            "interval_days": 30,
            "is_active": True,
        },
    )
    assert plan_response.status_code == 201
    plan_id = plan_response.json()["id"]

    response = await client.post(
        "/api/v1/maintenance-tasks/",
        json={
            "plan_id": plan_id,
            "equipment_id": equipment_id,
            "priority": "medium",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Maintenance plan equipment type does not match the target equipment."


async def test_maintenance_task_create_without_plan_requires_title(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "maintenance.manage"})

    equipment_type_id = await _create_equipment_type(client)
    equipment_id = await _create_equipment(client, equipment_type_id)

    response = await client.post(
        "/api/v1/maintenance-tasks/",
        json={
            "equipment_id": equipment_id,
            "priority": "medium",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Maintenance task title is required when plan_id is not provided."


async def test_maintenance_task_patch_rejects_done_status_direct_update(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "maintenance.manage"})

    equipment_type_id = await _create_equipment_type(client)
    equipment_id = await _create_equipment(client, equipment_type_id)

    create_task_response = await client.post(
        "/api/v1/maintenance-tasks/",
        json={
            "equipment_id": equipment_id,
            "title": "Ручная задача",
            "priority": "medium",
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response = await client.patch(
        f"/api/v1/maintenance-tasks/{task_id}",
        json={"status": "done"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Maintenance task completion must go through the completion endpoint."


async def test_maintenance_task_complete_rejects_second_completion(client, db_session, set_current_user):
    actor = await _create_user(db_session, email_prefix="maintenance_repeat_actor")
    await set_current_user(
        {"equipment.read", "equipment.manage", "maintenance.read", "maintenance.manage"},
        user_id=actor.id,
    )

    equipment_type_id = await _create_equipment_type(client)
    equipment_id = await _create_equipment(client, equipment_type_id)

    create_task_response = await client.post(
        "/api/v1/maintenance-tasks/",
        json={
            "equipment_id": equipment_id,
            "title": "Повторное завершение",
            "priority": "low",
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    first_complete_response = await client.post(
        f"/api/v1/maintenance-tasks/{task_id}/complete",
        json={
            "summary": "Первое завершение",
            "performed_at": datetime.now(UTC).isoformat(),
        },
    )
    assert first_complete_response.status_code == 201

    second_complete_response = await client.post(
        f"/api/v1/maintenance-tasks/{task_id}/complete",
        json={
            "summary": "Повторное завершение",
            "performed_at": datetime.now(UTC).isoformat(),
        },
    )
    assert second_complete_response.status_code == 400
    assert second_complete_response.json()["detail"] == "Maintenance task is already completed."


async def test_maintenance_task_list_filters_by_status(client, set_current_user):
    await set_current_user({"equipment.read", "equipment.manage", "maintenance.read", "maintenance.manage"})

    equipment_type_id = await _create_equipment_type(client)
    equipment_id = await _create_equipment(client, equipment_type_id)

    open_task_response = await client.post(
        "/api/v1/maintenance-tasks/",
        json={
            "equipment_id": equipment_id,
            "title": "Открытая задача",
            "priority": "medium",
        },
    )
    assert open_task_response.status_code == 201

    in_progress_task_response = await client.post(
        "/api/v1/maintenance-tasks/",
        json={
            "equipment_id": equipment_id,
            "title": "Задача в работе",
            "priority": "high",
        },
    )
    assert in_progress_task_response.status_code == 201
    in_progress_task_id = in_progress_task_response.json()["id"]

    patch_response = await client.patch(
        f"/api/v1/maintenance-tasks/{in_progress_task_id}",
        json={"status": "in_progress"},
    )
    assert patch_response.status_code == 200

    response = await client.get("/api/v1/maintenance-tasks/?status=in_progress")
    assert response.status_code == 200
    payload = response.json()
    assert any(item["id"] == in_progress_task_id for item in payload)
    assert all(item["status"] == "in_progress" for item in payload)


async def test_maintenance_task_list_rejects_unknown_status_filter(client, set_current_user):
    await set_current_user({"maintenance.read"})

    response = await client.get("/api/v1/maintenance-tasks/?status=queued")

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported maintenance task status filter."


async def test_maintenance_record_list_rejects_invalid_date_range(client, set_current_user):
    await set_current_user({"maintenance.read"})

    date_from = datetime.now(UTC)
    date_to = date_from - timedelta(days=1)

    response = await client.get(
        "/api/v1/maintenance-records/",
        params={
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "date_from must be less than or equal to date_to."


async def test_get_maintenance_entities_return_404_for_unknown_ids(client, set_current_user):
    await set_current_user({"maintenance.read"})

    plan_response = await client.get(f"/api/v1/maintenance-plans/{uuid4()}")
    task_response = await client.get(f"/api/v1/maintenance-tasks/{uuid4()}")
    record_response = await client.get(f"/api/v1/maintenance-records/{uuid4()}")

    assert plan_response.status_code == 404
    assert plan_response.json()["detail"] == "Maintenance plan not found."
    assert task_response.status_code == 404
    assert task_response.json()["detail"] == "Maintenance task not found."
    assert record_response.status_code == 404
    assert record_response.json()["detail"] == "Maintenance record not found."
