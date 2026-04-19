from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.audit import get_audit_service
from app.db.session import get_async_session
from app.dependencies.auth import get_current_user, require_permissions
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.notification import NotificationCreate, NotificationRead
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_notification_service(
    session: AsyncSession,
    background_tasks: BackgroundTasks | None = None,
) -> NotificationService:
    return NotificationService(
        NotificationRepository(session),
        UserRepository(session),
        background_tasks=background_tasks,
    )


@router.post("/manual", response_model=list[NotificationRead], status_code=status.HTTP_201_CREATED)
async def create_manual_notifications(
    payload: NotificationCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("notifications.manage")),
) -> list[NotificationRead]:
    service = get_notification_service(session, background_tasks)
    try:
        notifications = await service.create_manual_notifications(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="create",
        resource_type="notifications",
        resource_id=None,
        status_code=status.HTTP_201_CREATED,
        details=AuditService.build_details(
            request_data=payload.model_dump(mode="json", exclude_none=True),
            extra={"created_count": len(notifications), "mode": "manual"},
        ),
    )
    return [NotificationRead.model_validate(notification) for notification in notifications]


@router.get("/", response_model=list[NotificationRead], status_code=status.HTTP_200_OK)
async def list_notifications(
    channel: str | None = Query(default=None),
    notification_type: str | None = Query(default=None),
    is_read: bool | None = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("notifications.read")),
) -> list[NotificationRead]:
    service = get_notification_service(session)
    try:
        notifications = await service.list_notifications(
            current_user_id=current_user.id,
            channel=channel,
            notification_type=notification_type,
            is_read=is_read,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return [NotificationRead.model_validate(notification) for notification in notifications]


@router.get("/unread-count", status_code=status.HTTP_200_OK)
async def get_unread_count(
    channel: str | None = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("notifications.read")),
) -> dict[str, int]:
    service = get_notification_service(session)
    try:
        count = await service.get_unread_count(current_user_id=current_user.id, channel=channel)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return {"unread_count": count}


@router.get("/{notification_id}", response_model=NotificationRead, status_code=status.HTTP_200_OK)
async def get_notification(
    notification_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("notifications.read")),
) -> NotificationRead:
    service = get_notification_service(session)
    notification = await service.get_notification(notification_id, current_user_id=current_user.id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return NotificationRead.model_validate(notification)


@router.post("/{notification_id}/read", response_model=NotificationRead, status_code=status.HTTP_200_OK)
async def mark_notification_as_read(
    notification_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("notifications.read")),
) -> NotificationRead:
    service = get_notification_service(session)
    notification = await service.mark_as_read(notification_id, current_user_id=current_user.id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="mark_read",
        resource_type="notifications",
        resource_id=notification.id,
        status_code=status.HTTP_200_OK,
    )
    return NotificationRead.model_validate(notification)
