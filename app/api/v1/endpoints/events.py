from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.audit import get_audit_service
from app.db.session import get_async_session
from app.dependencies.auth import require_permissions
from app.repositories.event_repository import EventRepository
from app.repositories.equipment_repository import EquipmentRepository
from app.repositories.maintenance_plan_repository import MaintenancePlanRepository
from app.repositories.maintenance_record_repository import MaintenanceRecordRepository
from app.repositories.maintenance_task_repository import MaintenanceTaskRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.event import EventMaintenanceTaskCreate, EventRead
from app.schemas.maintenance import MaintenanceTaskCreate, MaintenanceTaskRead
from app.services.audit_service import AuditService
from app.services.event_service import EventService
from app.services.maintenance_task_service import MaintenanceTaskService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/events", tags=["Events"])


def get_event_service(session: AsyncSession) -> EventService:
    """Build the event service with its repository dependencies."""

    return EventService(
        EventRepository(session),
        NotificationService(NotificationRepository(session), UserRepository(session)),
    )


def get_maintenance_task_service(
    session: AsyncSession,
    background_tasks: BackgroundTasks | None = None,
) -> MaintenanceTaskService:
    """Build the maintenance task service used by event follow-up actions."""

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


@router.get("/", response_model=list[EventRead], status_code=status.HTTP_200_OK)
async def list_events(
    equipment_id: UUID | None = Query(default=None),
    parameter_id: UUID | None = Query(default=None),
    severity: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("events.read")),
) -> list[EventRead]:
    """Return monitoring events optionally filtered by equipment, parameter, severity, or type."""

    service = get_event_service(session)

    try:
        events = await service.list_events(
            equipment_id=equipment_id,
            parameter_id=parameter_id,
            severity=severity,
            event_type=event_type,
            limit=limit,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return [EventRead.model_validate(event) for event in events]


@router.get("/{event_id}", response_model=EventRead, status_code=status.HTTP_200_OK)
async def get_event(
    event_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("events.read")),
) -> EventRead:
    """Return a monitoring event by identifier."""

    service = get_event_service(session)
    event = await service.get_event(event_id)

    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

    return EventRead.model_validate(event)


@router.post(
    "/{event_id}/maintenance-task",
    response_model=MaintenanceTaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_maintenance_task_from_event(
    event_id: UUID,
    payload: EventMaintenanceTaskCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("events.read", "maintenance.manage")),
) -> MaintenanceTaskRead:
    """Create a maintenance task that uses the event equipment as the target."""

    event_service = get_event_service(session)
    event = await event_service.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

    title = payload.title or f"Проверить событие: {event.title}"
    base_description = (
        f"Создано из события {event.id}. "
        f"Тип: {event.event_type}. Критичность: {event.severity}. "
        f"Сообщение: {event.message}"
    )
    description = payload.description or base_description

    task_payload = MaintenanceTaskCreate(
        equipment_id=event.equipment_id,
        title=title,
        description=description[:500],
        priority=payload.priority,
        due_at=payload.due_at,
        assigned_to_user_id=payload.assigned_to_user_id,
    )

    service = get_maintenance_task_service(session, background_tasks)
    try:
        task = await service.create_task(task_payload, actor_user_id=current_user.id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="create_from_event",
        resource_type="maintenance_tasks",
        resource_id=task.id,
        status_code=status.HTTP_201_CREATED,
        details=AuditService.build_details(
            request_data=payload.model_dump(mode="json", exclude_none=True),
            extra={
                "event_id": str(event.id),
                "equipment_id": str(event.equipment_id),
                "event_type": event.event_type,
                "severity": event.severity,
            },
        ),
    )
    return MaintenanceTaskRead.model_validate(task)
