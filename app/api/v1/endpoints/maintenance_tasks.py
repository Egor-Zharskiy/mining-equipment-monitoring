from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.audit import get_audit_service
from app.db.session import get_async_session
from app.dependencies.auth import require_permissions
from app.repositories.equipment_repository import EquipmentRepository
from app.repositories.maintenance_plan_repository import MaintenancePlanRepository
from app.repositories.maintenance_record_repository import MaintenanceRecordRepository
from app.repositories.maintenance_task_repository import MaintenanceTaskRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.maintenance import (
    MaintenanceRecordRead,
    MaintenanceTaskComplete,
    MaintenanceTaskCreate,
    MaintenanceTaskRead,
    MaintenanceTaskUpdate,
)
from app.services.audit_service import AuditService
from app.services.maintenance_task_service import MaintenanceTaskService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/maintenance-tasks", tags=["Maintenance Tasks"])


def get_maintenance_task_service(
    session: AsyncSession,
    background_tasks: BackgroundTasks | None = None,
) -> MaintenanceTaskService:
    return MaintenanceTaskService(
        MaintenanceTaskRepository(session),
        MaintenancePlanRepository(session),
        MaintenanceRecordRepository(session),
        EquipmentRepository(session),
        UserRepository(session),
        NotificationService(
            NotificationRepository(session),
            UserRepository(session),
            background_tasks=background_tasks,
        ),
    )


@router.post("/", response_model=MaintenanceTaskRead, status_code=status.HTTP_201_CREATED)
async def create_maintenance_task(
    payload: MaintenanceTaskCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("maintenance.manage")),
) -> MaintenanceTaskRead:
    service = get_maintenance_task_service(session, background_tasks)
    try:
        task = await service.create_task(payload, actor_user_id=current_user.id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="create",
        resource_type="maintenance_tasks",
        resource_id=task.id,
        status_code=status.HTTP_201_CREATED,
        details=AuditService.build_details(
            request_data=payload.model_dump(mode="json", exclude_none=True),
        ),
    )
    return MaintenanceTaskRead.model_validate(task)


@router.get("/", response_model=list[MaintenanceTaskRead], status_code=status.HTTP_200_OK)
async def list_maintenance_tasks(
    equipment_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    assigned_to_user_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("maintenance.read")),
) -> list[MaintenanceTaskRead]:
    service = get_maintenance_task_service(session)
    try:
        tasks = await service.list_tasks(
            equipment_id=equipment_id,
            status=status_filter,
            priority=priority,
            assigned_to_user_id=assigned_to_user_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return [MaintenanceTaskRead.model_validate(task) for task in tasks]


@router.get("/{task_id}", response_model=MaintenanceTaskRead, status_code=status.HTTP_200_OK)
async def get_maintenance_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("maintenance.read")),
) -> MaintenanceTaskRead:
    service = get_maintenance_task_service(session)
    task = await service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance task not found.")
    return MaintenanceTaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=MaintenanceTaskRead, status_code=status.HTTP_200_OK)
async def update_maintenance_task(
    task_id: UUID,
    payload: MaintenanceTaskUpdate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("maintenance.manage")),
) -> MaintenanceTaskRead:
    service = get_maintenance_task_service(session, background_tasks)
    try:
        task = await service.update_task(task_id, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance task not found.")
    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="update",
        resource_type="maintenance_tasks",
        resource_id=task.id,
        status_code=status.HTTP_200_OK,
        details=AuditService.build_details(
            request_data=payload.model_dump(mode="json", exclude_none=True),
        ),
    )
    return MaintenanceTaskRead.model_validate(task)


@router.post("/{task_id}/complete", response_model=MaintenanceRecordRead, status_code=status.HTTP_201_CREATED)
async def complete_maintenance_task(
    task_id: UUID,
    payload: MaintenanceTaskComplete,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("maintenance.manage")),
) -> MaintenanceRecordRead:
    service = get_maintenance_task_service(session)
    try:
        record = await service.complete_task(task_id, payload, actor_user_id=current_user.id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance task not found.")
    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="complete",
        resource_type="maintenance_tasks",
        resource_id=record.task.id,
        status_code=status.HTTP_201_CREATED,
        details=AuditService.build_details(
            request_data=payload.model_dump(mode="json", exclude_none=True),
            extra={"maintenance_record_id": str(record.id)},
        ),
    )
    return MaintenanceRecordRead.model_validate(record)
