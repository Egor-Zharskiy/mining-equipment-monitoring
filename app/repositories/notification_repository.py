from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Equipment, Event, MaintenancePlan, MaintenanceTask, Notification, User

UNSET = object()


class NotificationRepository:
    """Handles database access for notifications."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        recipient_user: User,
        event: Event | None,
        maintenance_task: MaintenanceTask | None,
        notification_type: str,
        channel: str,
        title: str,
        message: str,
        delivered_at: datetime | None,
    ) -> Notification:
        notification = Notification(
            recipient_user=recipient_user,
            event=event,
            maintenance_task=maintenance_task,
            notification_type=notification_type,
            channel=channel,
            title=title,
            message=message,
            delivered_at=delivered_at,
        )
        self._session.add(notification)
        await self._session.flush()
        await self._session.refresh(notification)
        return await self.get_by_id(notification.id)  # type: ignore[return-value]

    async def get_by_id(self, notification_id: UUID) -> Notification | None:
        result = await self._session.execute(
            select(Notification)
            .options(
                joinedload(Notification.recipient_user),
                joinedload(Notification.event).joinedload(Event.equipment).joinedload(Equipment.equipment_type),
                joinedload(Notification.event).joinedload(Event.parameter),
                joinedload(Notification.maintenance_task).joinedload(MaintenanceTask.plan).joinedload(MaintenancePlan.equipment_type),
                joinedload(Notification.maintenance_task).joinedload(MaintenanceTask.plan).joinedload(MaintenancePlan.equipment).joinedload(Equipment.equipment_type),
                joinedload(Notification.maintenance_task).joinedload(MaintenanceTask.equipment).joinedload(Equipment.equipment_type),
                joinedload(Notification.maintenance_task).joinedload(MaintenanceTask.created_by_user),
                joinedload(Notification.maintenance_task).joinedload(MaintenanceTask.assigned_to_user),
            )
            .where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        *,
        recipient_user_id: UUID,
        channel: str | None = None,
        notification_type: str | None = None,
        is_read: bool | None = None,
    ) -> list[Notification]:
        query = select(Notification).options(
            joinedload(Notification.recipient_user),
            joinedload(Notification.event).joinedload(Event.equipment).joinedload(Equipment.equipment_type),
            joinedload(Notification.event).joinedload(Event.parameter),
            joinedload(Notification.maintenance_task).joinedload(MaintenanceTask.plan).joinedload(MaintenancePlan.equipment_type),
            joinedload(Notification.maintenance_task).joinedload(MaintenanceTask.plan).joinedload(MaintenancePlan.equipment).joinedload(Equipment.equipment_type),
            joinedload(Notification.maintenance_task).joinedload(MaintenanceTask.equipment).joinedload(Equipment.equipment_type),
            joinedload(Notification.maintenance_task).joinedload(MaintenanceTask.created_by_user),
            joinedload(Notification.maintenance_task).joinedload(MaintenanceTask.assigned_to_user),
        ).where(Notification.recipient_user_id == recipient_user_id)

        if channel is not None:
            query = query.where(Notification.channel == channel)
        if notification_type is not None:
            query = query.where(Notification.notification_type == notification_type)
        if is_read is not None:
            query = query.where(Notification.is_read == is_read)

        result = await self._session.execute(query.order_by(Notification.created_at.desc()))
        return list(result.scalars().unique().all())

    async def update(
        self,
        notification: Notification,
        *,
        is_read: bool | object = UNSET,
        read_at: datetime | None | object = UNSET,
        delivered_at: datetime | None | object = UNSET,
    ) -> Notification:
        if is_read is not UNSET:
            notification.is_read = is_read  # type: ignore[assignment]
        if read_at is not UNSET:
            notification.read_at = read_at  # type: ignore[assignment]
        if delivered_at is not UNSET:
            notification.delivered_at = delivered_at  # type: ignore[assignment]

        await self._session.flush()
        await self._session.refresh(notification)
        return await self.get_by_id(notification.id)  # type: ignore[return-value]

    async def count_unread_for_user(self, recipient_user_id: UUID, *, channel: str | None = None) -> int:
        query = select(func.count(Notification.id)).where(
            Notification.recipient_user_id == recipient_user_id,
            Notification.is_read.is_(False),
        )
        if channel is not None:
            query = query.where(Notification.channel == channel)

        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def exists_for_source(
        self,
        *,
        recipient_user_id: UUID,
        notification_type: str,
        channel: str,
        event_id: UUID | None = None,
        maintenance_task_id: UUID | None = None,
    ) -> bool:
        query = select(Notification.id).where(
            Notification.recipient_user_id == recipient_user_id,
            Notification.notification_type == notification_type,
            Notification.channel == channel,
        )
        if event_id is not None:
            query = query.where(Notification.event_id == event_id)
        if maintenance_task_id is not None:
            query = query.where(Notification.maintenance_task_id == maintenance_task_id)

        result = await self._session.execute(query.limit(1))
        return result.scalar_one_or_none() is not None
