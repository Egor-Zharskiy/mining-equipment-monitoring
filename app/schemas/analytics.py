from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.equipment import EquipmentRead
from app.schemas.parameter import ParameterRead


class AnalyticsPeriodRead(BaseModel):
    """Time range used to build an analytics response."""

    date_from: datetime | None
    date_to: datetime | None


class EquipmentStatusByTypeRead(BaseModel):
    """Equipment status breakdown for a single equipment type."""

    equipment_type_id: UUID
    equipment_type_name: str
    total_count: int
    by_status: dict[str, int]


class EquipmentStatusAnalyticsRead(BaseModel):
    """Current equipment-state distribution for the dashboard."""

    total_count: int
    by_status: dict[str, int]
    by_type: list[EquipmentStatusByTypeRead]


class EventTimelinePointRead(BaseModel):
    """Number of events produced on a calendar day."""

    date: date
    count: int


class EventAnalyticsRead(BaseModel):
    """Event distribution for dashboards and trend widgets."""

    period: AnalyticsPeriodRead
    total_count: int
    by_severity: dict[str, int]
    by_event_type: dict[str, int]
    timeline: list[EventTimelinePointRead]


class TelemetryHistoryPointRead(BaseModel):
    """Single telemetry point for charting."""

    reading_id: UUID
    measured_at: datetime
    value: Decimal
    status: str | None


class TelemetryHistorySummaryRead(BaseModel):
    """Basic telemetry summary statistics for a selected series."""

    point_count: int
    min_value: Decimal | None
    max_value: Decimal | None
    avg_value: Decimal | None


class TelemetryHistoryAnalyticsRead(BaseModel):
    """Telemetry history and summary for chart widgets."""

    equipment: EquipmentRead
    parameter: ParameterRead
    period: AnalyticsPeriodRead
    summary: TelemetryHistorySummaryRead
    points: list[TelemetryHistoryPointRead]


class MaintenanceAnalyticsRead(BaseModel):
    """Maintenance workload summary."""

    total_count: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    overdue_count: int
    upcoming_count: int
    completed_count: int


class NotificationAnalyticsRead(BaseModel):
    """Notification summary across channels and types."""

    period: AnalyticsPeriodRead
    total_count: int
    unread_count: int
    by_channel: dict[str, int]
    by_type: dict[str, int]
    by_read_state: dict[str, int]


class AnalyticsOverviewSectionRead(BaseModel):
    """Compact overview section based on simple totals and buckets."""

    total_count: int
    buckets: dict[str, int]


class AnalyticsOverviewRead(BaseModel):
    """High-level dashboard payload."""

    period: AnalyticsPeriodRead
    equipment: AnalyticsOverviewSectionRead
    events: AnalyticsOverviewSectionRead
    maintenance: AnalyticsOverviewSectionRead
    notifications: AnalyticsOverviewSectionRead
