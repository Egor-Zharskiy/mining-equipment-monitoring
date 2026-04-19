from collections import Counter
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from app.core.events import VALID_EVENT_TYPES
from app.core.maintenance import VALID_MAINTENANCE_TASK_PRIORITIES, VALID_MAINTENANCE_TASK_STATUSES
from app.core.monitoring import VALID_MONITORING_STATUSES
from app.core.notifications import VALID_NOTIFICATION_CHANNELS, VALID_NOTIFICATION_TYPES
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.equipment_repository import EquipmentRepository
from app.repositories.equipment_type_repository import EquipmentTypeRepository
from app.repositories.parameter_repository import ParameterRepository
from app.repositories.user_repository import UserRepository
from app.schemas.analytics import (
    AnalyticsOverviewRead,
    AnalyticsOverviewSectionRead,
    AnalyticsPeriodRead,
    EquipmentStatusAnalyticsRead,
    EquipmentStatusByTypeRead,
    EventAnalyticsRead,
    EventTimelinePointRead,
    MaintenanceAnalyticsRead,
    NotificationAnalyticsRead,
    TelemetryHistoryAnalyticsRead,
    TelemetryHistoryPointRead,
    TelemetryHistorySummaryRead,
)

ANALYTICS_EQUIPMENT_STATUS_UNKNOWN = "unknown"
ANALYTICS_DEFAULT_OVERVIEW_DAYS = 7
ANALYTICS_UPCOMING_WINDOW_DAYS = 3


class AnalyticsService:
    """Builds read-only analytics payloads for dashboard endpoints."""

    def __init__(
        self,
        analytics_repository: AnalyticsRepository,
        equipment_repository: EquipmentRepository,
        equipment_type_repository: EquipmentTypeRepository,
        parameter_repository: ParameterRepository,
        user_repository: UserRepository,
    ) -> None:
        self._analytics_repository = analytics_repository
        self._equipment_repository = equipment_repository
        self._equipment_type_repository = equipment_type_repository
        self._parameter_repository = parameter_repository
        self._user_repository = user_repository

    async def get_overview(self, *, days: int = ANALYTICS_DEFAULT_OVERVIEW_DAYS) -> AnalyticsOverviewRead:
        now = datetime.now(UTC)
        date_from = now - timedelta(days=days)

        equipment_analytics = await self.get_equipment_status_analytics()
        event_analytics = await self.get_event_analytics(date_from=date_from, date_to=now)
        maintenance_analytics = await self.get_maintenance_analytics()
        notification_analytics = await self.get_notification_analytics(date_from=date_from, date_to=now)

        return AnalyticsOverviewRead(
            period=AnalyticsPeriodRead(date_from=date_from, date_to=now),
            equipment=AnalyticsOverviewSectionRead(
                total_count=equipment_analytics.total_count,
                buckets=equipment_analytics.by_status,
            ),
            events=AnalyticsOverviewSectionRead(
                total_count=event_analytics.total_count,
                buckets=event_analytics.by_severity,
            ),
            maintenance=AnalyticsOverviewSectionRead(
                total_count=maintenance_analytics.total_count,
                buckets=maintenance_analytics.by_status,
            ),
            notifications=AnalyticsOverviewSectionRead(
                total_count=notification_analytics.total_count,
                buckets=notification_analytics.by_channel,
            ),
        )

    async def get_equipment_status_analytics(
        self,
        *,
        equipment_type_id: UUID | None = None,
    ) -> EquipmentStatusAnalyticsRead:
        if equipment_type_id is not None:
            equipment_type = await self._equipment_type_repository.get_by_id(equipment_type_id)
            if equipment_type is None:
                raise ValueError("Equipment type filter references an unknown equipment type.")

        rows = await self._analytics_repository.list_equipment_status_rows(
            equipment_type_id=equipment_type_id,
        )

        total_by_status: Counter[str] = Counter()
        by_type_index: dict[UUID, EquipmentStatusByTypeRead] = {}

        for type_id, type_name, raw_status in rows:
            status = raw_status or ANALYTICS_EQUIPMENT_STATUS_UNKNOWN
            total_by_status[status] += 1

            if type_id not in by_type_index:
                by_type_index[type_id] = EquipmentStatusByTypeRead(
                    equipment_type_id=type_id,
                    equipment_type_name=type_name,
                    total_count=0,
                    by_status={},
                )
            entry = by_type_index[type_id]
            entry.total_count += 1
            entry.by_status[status] = entry.by_status.get(status, 0) + 1

        valid_statuses = (*VALID_MONITORING_STATUSES, ANALYTICS_EQUIPMENT_STATUS_UNKNOWN)
        for entry in by_type_index.values():
            entry.by_status = self._with_zero_buckets(Counter(entry.by_status), valid_statuses)

        return EquipmentStatusAnalyticsRead(
            total_count=len(rows),
            by_status=self._with_zero_buckets(total_by_status, valid_statuses),
            by_type=list(by_type_index.values()),
        )

    async def get_event_analytics(
        self,
        *,
        equipment_id: UUID | None = None,
        severity: str | None = None,
        event_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> EventAnalyticsRead:
        self._validate_date_range(date_from=date_from, date_to=date_to)
        if severity is not None and severity not in VALID_MONITORING_STATUSES:
            raise ValueError("Unsupported event severity filter.")
        if event_type is not None and event_type not in VALID_EVENT_TYPES:
            raise ValueError("Unsupported event type filter.")
        if equipment_id is not None:
            equipment = await self._equipment_repository.get_by_id(equipment_id)
            if equipment is None:
                raise ValueError("Equipment filter references an unknown equipment item.")

        rows = await self._analytics_repository.list_event_rows(
            equipment_id=equipment_id,
            severity=severity,
            event_type=event_type,
            date_from=date_from,
            date_to=date_to,
        )

        severity_counts: Counter[str] = Counter()
        event_type_counts: Counter[str] = Counter()
        timeline_counts: Counter[date] = Counter()

        for row_severity, row_event_type, created_at in rows:
            severity_counts[row_severity] += 1
            event_type_counts[row_event_type] += 1
            timeline_counts[created_at.date()] += 1

        return EventAnalyticsRead(
            period=AnalyticsPeriodRead(date_from=date_from, date_to=date_to),
            total_count=len(rows),
            by_severity=self._with_zero_buckets(severity_counts, VALID_MONITORING_STATUSES),
            by_event_type=self._with_zero_buckets(event_type_counts, VALID_EVENT_TYPES),
            timeline=[
                EventTimelinePointRead(date=event_date, count=count)
                for event_date, count in sorted(timeline_counts.items())
            ],
        )

    async def get_telemetry_history_analytics(
        self,
        *,
        equipment_id: UUID,
        parameter_id: UUID,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 200,
    ) -> TelemetryHistoryAnalyticsRead:
        self._validate_date_range(date_from=date_from, date_to=date_to)

        equipment = await self._equipment_repository.get_by_id(equipment_id)
        if equipment is None:
            raise ValueError("Telemetry history references an unknown equipment item.")

        parameter = await self._parameter_repository.get_by_id(parameter_id)
        if parameter is None:
            raise ValueError("Telemetry history references an unknown parameter.")

        readings = await self._analytics_repository.list_telemetry_history(
            equipment_id=equipment_id,
            parameter_id=parameter_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )

        points = [
            TelemetryHistoryPointRead(
                reading_id=reading.id,
                measured_at=reading.measured_at,
                value=reading.value,
                status=reading.evaluation.status if reading.evaluation is not None else None,
            )
            for reading in reversed(readings)
        ]

        values = [point.value for point in points]
        average_value = (sum(values, start=Decimal("0")) / Decimal(len(values))) if values else None

        return TelemetryHistoryAnalyticsRead(
            equipment=equipment,
            parameter=parameter,
            period=AnalyticsPeriodRead(date_from=date_from, date_to=date_to),
            summary=TelemetryHistorySummaryRead(
                point_count=len(points),
                min_value=min(values) if values else None,
                max_value=max(values) if values else None,
                avg_value=average_value,
            ),
            points=points,
        )

    async def get_maintenance_analytics(
        self,
        *,
        equipment_id: UUID | None = None,
    ) -> MaintenanceAnalyticsRead:
        if equipment_id is not None:
            equipment = await self._equipment_repository.get_by_id(equipment_id)
            if equipment is None:
                raise ValueError("Maintenance analytics references an unknown equipment item.")

        rows = await self._analytics_repository.list_maintenance_rows(equipment_id=equipment_id)

        now = datetime.now(UTC)
        status_counts: Counter[str] = Counter()
        priority_counts: Counter[str] = Counter()
        overdue_count = 0
        upcoming_count = 0
        completed_count = 0

        for status, priority, due_at, completed_at in rows:
            status_counts[status] += 1
            priority_counts[priority] += 1
            if completed_at is not None:
                completed_count += 1
            if status in {"open", "in_progress"} and due_at is not None:
                if due_at < now:
                    overdue_count += 1
                elif due_at <= now + timedelta(days=ANALYTICS_UPCOMING_WINDOW_DAYS):
                    upcoming_count += 1

        return MaintenanceAnalyticsRead(
            total_count=len(rows),
            by_status=self._with_zero_buckets(status_counts, VALID_MAINTENANCE_TASK_STATUSES),
            by_priority=self._with_zero_buckets(priority_counts, VALID_MAINTENANCE_TASK_PRIORITIES),
            overdue_count=overdue_count,
            upcoming_count=upcoming_count,
            completed_count=completed_count,
        )

    async def get_notification_analytics(
        self,
        *,
        recipient_user_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> NotificationAnalyticsRead:
        self._validate_date_range(date_from=date_from, date_to=date_to)
        if recipient_user_id is not None:
            user = await self._user_repository.get_by_id(recipient_user_id)
            if user is None:
                raise ValueError("Notification analytics references an unknown recipient user.")

        rows = await self._analytics_repository.list_notification_rows(
            recipient_user_id=recipient_user_id,
            date_from=date_from,
            date_to=date_to,
        )

        channel_counts: Counter[str] = Counter()
        type_counts: Counter[str] = Counter()
        read_state_counts: Counter[str] = Counter()
        unread_count = 0

        for channel, notification_type, is_read, _created_at in rows:
            channel_counts[channel] += 1
            type_counts[notification_type] += 1
            read_state = "read" if is_read else "unread"
            read_state_counts[read_state] += 1
            if not is_read:
                unread_count += 1

        return NotificationAnalyticsRead(
            period=AnalyticsPeriodRead(date_from=date_from, date_to=date_to),
            total_count=len(rows),
            unread_count=unread_count,
            by_channel=self._with_zero_buckets(channel_counts, VALID_NOTIFICATION_CHANNELS),
            by_type=self._with_zero_buckets(type_counts, VALID_NOTIFICATION_TYPES),
            by_read_state=self._with_zero_buckets(read_state_counts, ("read", "unread")),
        )

    @staticmethod
    def _validate_date_range(*, date_from: datetime | None, date_to: datetime | None) -> None:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise ValueError("Invalid date range: date_from must be less than or equal to date_to.")

    @staticmethod
    def _with_zero_buckets(counter: Counter[str], valid_values: tuple[str, ...]) -> dict[str, int]:
        buckets = {value: 0 for value in valid_values}
        buckets.update(counter)
        return buckets
