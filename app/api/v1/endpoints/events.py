from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.dependencies.auth import require_permissions
from app.repositories.event_repository import EventRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.event import EventRead
from app.services.event_service import EventService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/events", tags=["Events"])


def get_event_service(session: AsyncSession) -> EventService:
    """Build the event service with its repository dependencies."""

    return EventService(
        EventRepository(session),
        NotificationService(NotificationRepository(session), UserRepository(session)),
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
