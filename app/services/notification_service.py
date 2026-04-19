import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.exc import SQLAlchemyError

from app.config import app_config
from app.core.notifications import (
    NOTIFICATION_CHANNEL_EMAIL,
    NOTIFICATION_CHANNEL_INTERNAL,
    NOTIFICATION_TYPE_EVENT_CRITICAL,
    NOTIFICATION_TYPE_EVENT_WARNING,
    NOTIFICATION_TYPE_MANUAL,
    NOTIFICATION_TYPE_UPCOMING_MAINTENANCE,
    UPCOMING_MAINTENANCE_WINDOW_DAYS,
    VALID_NOTIFICATION_CHANNELS,
    VALID_NOTIFICATION_TYPES,
)
from app.core.monitoring import METRIC_STATUS_CRITICAL, METRIC_STATUS_WARNING
from app.db.session import get_async_session_maker
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.notification import NotificationCreate
from app.services.email_service import EmailDeliveryError, EmailService

logger = logging.getLogger(__name__)


class NotificationService:
    """Encapsulates generation and querying of user notifications."""

    def __init__(
        self,
        notification_repository: NotificationRepository,
        user_repository: UserRepository,
        email_service: EmailService | None = None,
        background_tasks: BackgroundTasks | None = None,
    ) -> None:
        self._notification_repository = notification_repository
        self._user_repository = user_repository
        self._email_service = email_service or EmailService()
        self._background_tasks = background_tasks

    async def notify_for_event(self, event) -> None:
        if not app_config.runtime_notifications_enabled:
            return

        notification_type = self._map_event_notification_type(event.severity)
        if notification_type is None:
            return

        recipients = await self._user_repository.get_active_with_permission("notifications.read")
        for recipient in recipients:
            for channel in VALID_NOTIFICATION_CHANNELS:
                if await self._notification_repository.exists_for_source(
                    recipient_user_id=recipient.id,
                    notification_type=notification_type,
                    channel=channel,
                    event_id=event.id,
                ):
                    continue
                await self._create_notification(
                    recipient_user=recipient,
                    event=event,
                    maintenance_task=None,
                    notification_type=notification_type,
                    channel=channel,
                    title=self._build_event_title(event.severity, event.title),
                    message=event.message,
                )

    async def notify_for_upcoming_maintenance(self, task) -> None:
        if not app_config.runtime_notifications_enabled:
            return

        if task.status not in {"open", "in_progress"}:
            return
        if task.due_at is None:
            return
        now = datetime.now(UTC)
        if task.due_at < now:
            return
        if task.due_at > now + timedelta(days=UPCOMING_MAINTENANCE_WINDOW_DAYS):
            return

        recipients = []
        if task.assigned_to_user is not None and task.assigned_to_user.is_active:
            recipients.append(task.assigned_to_user)
        elif task.created_by_user is not None and task.created_by_user.is_active:
            recipients.append(task.created_by_user)
        else:
            recipients = await self._user_repository.get_active_with_permission("notifications.read")

        for recipient in recipients:
            for channel in VALID_NOTIFICATION_CHANNELS:
                if await self._notification_repository.exists_for_source(
                    recipient_user_id=recipient.id,
                    notification_type=NOTIFICATION_TYPE_UPCOMING_MAINTENANCE,
                    channel=channel,
                    maintenance_task_id=task.id,
                ):
                    continue
                await self._create_notification(
                    recipient_user=recipient,
                    event=None,
                    maintenance_task=task,
                    notification_type=NOTIFICATION_TYPE_UPCOMING_MAINTENANCE,
                    channel=channel,
                    title="Предстоящее техническое обслуживание",
                    message=(
                        f"Задача '{task.title}' для оборудования '{task.equipment.name}' "
                        f"требует внимания до {task.due_at.isoformat()}."
                    ),
                )

    async def create_manual_notifications(self, payload: NotificationCreate):
        channels = self._validate_channels(payload.channels)
        recipients = await self._user_repository.get_many_by_ids(payload.recipient_user_ids)
        if len(recipients) != len(set(payload.recipient_user_ids)):
            raise ValueError("One or more notification recipients were not found.")

        created_notifications = []
        for recipient in recipients:
            for channel in channels:
                created_notifications.append(
                    await self._create_notification(
                        recipient_user=recipient,
                        event=None,
                        maintenance_task=None,
                        notification_type=NOTIFICATION_TYPE_MANUAL,
                        channel=channel,
                        title=payload.title,
                        message=payload.message,
                    )
                )
        return created_notifications

    async def _create_notification(
        self,
        *,
        recipient_user,
        event,
        maintenance_task,
        notification_type: str,
        channel: str,
        title: str,
        message: str,
    ):
        notification = await self._notification_repository.create(
            recipient_user=recipient_user,
            event=event,
            maintenance_task=maintenance_task,
            notification_type=notification_type,
            channel=channel,
            title=title,
            message=message,
            delivered_at=self._resolve_initial_delivered_at(channel),
        )

        if channel != NOTIFICATION_CHANNEL_EMAIL:
            return notification

        if self._background_tasks is not None:
            self._background_tasks.add_task(
                self._deliver_email_notification_snapshot,
                notification_id=notification.id,
                to_email=notification.recipient_user.email,
                subject=notification.title,
                body=self._build_email_body(notification),
            )
            return notification

        delivered_at = await self._deliver_email_notification(notification)
        if delivered_at is None:
            return notification

        return await self._notification_repository.update(
            notification,
            delivered_at=delivered_at,
        )

    async def list_notifications(self, *, current_user_id: UUID, channel: str | None = None, notification_type: str | None = None, is_read: bool | None = None):
        if channel is not None and channel not in VALID_NOTIFICATION_CHANNELS:
            raise ValueError("Unsupported notification channel filter.")
        if notification_type is not None and notification_type not in VALID_NOTIFICATION_TYPES:
            raise ValueError("Unsupported notification type filter.")

        effective_channel = channel or NOTIFICATION_CHANNEL_INTERNAL
        return await self._notification_repository.list_for_user(
            recipient_user_id=current_user_id,
            channel=effective_channel,
            notification_type=notification_type,
            is_read=is_read,
        )

    async def get_notification(self, notification_id: UUID, *, current_user_id: UUID):
        notification = await self._notification_repository.get_by_id(notification_id)
        if notification is None or notification.recipient_user_id != current_user_id:
            return None
        return notification

    async def mark_as_read(self, notification_id: UUID, *, current_user_id: UUID):
        notification = await self.get_notification(notification_id, current_user_id=current_user_id)
        if notification is None:
            return None
        if notification.is_read:
            return notification

        return await self._notification_repository.update(
            notification,
            is_read=True,
            read_at=datetime.now(UTC),
        )

    async def get_unread_count(self, *, current_user_id: UUID, channel: str | None = None) -> int:
        if channel is not None and channel not in VALID_NOTIFICATION_CHANNELS:
            raise ValueError("Unsupported notification channel filter.")

        effective_channel = channel or NOTIFICATION_CHANNEL_INTERNAL
        return await self._notification_repository.count_unread_for_user(
            current_user_id,
            channel=effective_channel,
        )

    @staticmethod
    def _map_event_notification_type(severity: str) -> str | None:
        if severity == METRIC_STATUS_CRITICAL:
            return NOTIFICATION_TYPE_EVENT_CRITICAL
        if severity == METRIC_STATUS_WARNING:
            return NOTIFICATION_TYPE_EVENT_WARNING
        return None

    @staticmethod
    def _build_event_title(severity: str, fallback_title: str) -> str:
        if severity == METRIC_STATUS_CRITICAL:
            return f"Критическое событие: {fallback_title}"
        if severity == METRIC_STATUS_WARNING:
            return f"Предупреждение: {fallback_title}"
        return fallback_title

    @staticmethod
    def _validate_channels(channels: list[str]) -> list[str]:
        unique_channels = list(dict.fromkeys(channels))
        if any(channel not in VALID_NOTIFICATION_CHANNELS for channel in unique_channels):
            raise ValueError("Unsupported notification channel.")
        return unique_channels

    def _resolve_initial_delivered_at(self, channel: str) -> datetime | None:
        if channel == NOTIFICATION_CHANNEL_INTERNAL:
            return datetime.now(UTC)
        return None

    async def _deliver_email_notification(self, notification) -> datetime | None:
        return await self._send_email_notification(
            notification_id=notification.id,
            to_email=notification.recipient_user.email,
            subject=notification.title,
            body=self._build_email_body(notification),
        )

    async def _deliver_email_notification_snapshot(
        self,
        *,
        notification_id: UUID,
        to_email: str,
        subject: str,
        body: str,
    ) -> None:
        delivered_at = await self._send_email_notification(
            notification_id=notification_id,
            to_email=to_email,
            subject=subject,
            body=body,
        )
        if delivered_at is None:
            return

        await self._mark_email_notification_delivered(notification_id, delivered_at)

    async def _send_email_notification(
        self,
        *,
        notification_id: UUID,
        to_email: str,
        subject: str,
        body: str,
    ) -> datetime | None:
        try:
            delivered = await self._email_service.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
            )
        except EmailDeliveryError:
            logger.exception(
                "Email notification delivery failed.",
                extra={"notification_id": str(notification_id)},
            )
            return None

        if not delivered:
            return None
        return datetime.now(UTC)

    async def _mark_email_notification_delivered(self, notification_id: UUID, delivered_at: datetime) -> None:
        session_maker = get_async_session_maker()
        if session_maker is None:
            logger.error(
                "Email notification delivery status cannot be persisted because database is not configured.",
                extra={"notification_id": str(notification_id)},
            )
            return

        async with session_maker() as session:
            repository = NotificationRepository(session)
            try:
                notification = await repository.get_by_id(notification_id)
                if notification is None:
                    updated = await self._mark_email_notification_delivered_in_current_session(
                        notification_id,
                        delivered_at,
                    )
                    if not updated:
                        logger.warning(
                            "Email notification was delivered but notification row was not found.",
                            extra={"notification_id": str(notification_id)},
                        )
                    return

                await repository.update(notification, delivered_at=delivered_at)
                await session.commit()
            except SQLAlchemyError:
                await session.rollback()
                logger.exception(
                    "Email notification delivery status update failed.",
                    extra={"notification_id": str(notification_id)},
                )

    async def _mark_email_notification_delivered_in_current_session(
        self,
        notification_id: UUID,
        delivered_at: datetime,
    ) -> bool:
        try:
            notification = await self._notification_repository.get_by_id(notification_id)
            if notification is None:
                return False

            await self._notification_repository.update(notification, delivered_at=delivered_at)
            return True
        except SQLAlchemyError:
            logger.exception(
                "Email notification delivery status fallback update failed.",
                extra={"notification_id": str(notification_id)},
            )
            return False

    @staticmethod
    def _build_email_body(notification) -> str:
        lines = [
            notification.message,
            "",
            "Система: Mining Equipment Monitoring",
            f"Тип уведомления: {notification.notification_type}",
        ]
        if notification.event is not None:
            lines.append(f"Событие: {notification.event.event_type}")
        if notification.maintenance_task is not None:
            lines.append(f"Задача ТО: {notification.maintenance_task.title}")
        return "\n".join(lines)
