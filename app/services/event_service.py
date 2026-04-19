from app.core.events import (
    EVENT_TYPE_EQUIPMENT_CRITICAL,
    EVENT_TYPE_EQUIPMENT_RECOVERED,
    EVENT_TYPE_EQUIPMENT_WARNING,
    EVENT_TYPE_PARAMETER_CRITICAL,
    EVENT_TYPE_PARAMETER_RECOVERED,
    EVENT_TYPE_PARAMETER_WARNING,
    VALID_EVENT_TYPES,
)
from app.core.monitoring import (
    METRIC_STATUS_CRITICAL,
    METRIC_STATUS_NORMAL,
    METRIC_STATUS_WARNING,
    VALID_MONITORING_STATUSES,
)
from app.repositories.event_repository import EventRepository
from app.services.notification_service import NotificationService


class EventService:
    """Encapsulates generation and querying of monitoring events."""

    def __init__(
        self,
        event_repository: EventRepository,
        notification_service: NotificationService | None = None,
    ) -> None:
        """Store repository dependencies used by the service."""

        self._event_repository = event_repository
        self._notification_service = notification_service

    async def create_transition_events(
        self,
        *,
        equipment,
        parameter,
        telemetry_reading,
        previous_parameter_status: str | None,
        new_parameter_status: str,
        previous_equipment_status: str | None,
        new_equipment_status: str,
    ) -> None:
        """Create monitoring events for meaningful metric and equipment state transitions."""

        parameter_event = self._build_parameter_event(
            equipment=equipment,
            parameter=parameter,
            previous_status=previous_parameter_status,
            new_status=new_parameter_status,
        )
        if parameter_event is not None:
            created_event = await self._event_repository.create(
                equipment=equipment,
                parameter=parameter,
                telemetry_reading=telemetry_reading,
                event_type=parameter_event["event_type"],
                severity=parameter_event["severity"],
                title=parameter_event["title"],
                message=parameter_event["message"],
            )
            if self._notification_service is not None:
                await self._notification_service.notify_for_event(created_event)

        equipment_event = self._build_equipment_event(
            equipment=equipment,
            previous_status=previous_equipment_status,
            new_status=new_equipment_status,
        )
        if equipment_event is not None:
            created_event = await self._event_repository.create(
                equipment=equipment,
                parameter=None,
                telemetry_reading=telemetry_reading,
                event_type=equipment_event["event_type"],
                severity=equipment_event["severity"],
                title=equipment_event["title"],
                message=equipment_event["message"],
            )
            if self._notification_service is not None:
                await self._notification_service.notify_for_event(created_event)

    async def list_events(
        self,
        *,
        equipment_id=None,
        parameter_id=None,
        severity: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ):
        """Return monitoring events with optional filtering."""

        if severity is not None and severity not in VALID_MONITORING_STATUSES:
            raise ValueError("Unsupported event severity filter.")
        if event_type is not None and event_type not in VALID_EVENT_TYPES:
            raise ValueError("Unsupported event type filter.")

        return await self._event_repository.list_all(
            equipment_id=equipment_id,
            parameter_id=parameter_id,
            severity=severity,
            event_type=event_type,
            limit=limit,
        )

    async def get_event(self, event_id):
        """Return a monitoring event by identifier."""

        return await self._event_repository.get_by_id(event_id)

    @staticmethod
    def _build_parameter_event(*, equipment, parameter, previous_status: str | None, new_status: str):
        if new_status == METRIC_STATUS_WARNING and previous_status != METRIC_STATUS_WARNING:
            return {
                "event_type": EVENT_TYPE_PARAMETER_WARNING,
                "severity": METRIC_STATUS_WARNING,
                "title": "Параметр перешел в предупреждение",
                "message": f"Параметр '{parameter.name}' оборудования '{equipment.name}' вошел в зону warning.",
            }
        if new_status == METRIC_STATUS_CRITICAL and previous_status != METRIC_STATUS_CRITICAL:
            return {
                "event_type": EVENT_TYPE_PARAMETER_CRITICAL,
                "severity": METRIC_STATUS_CRITICAL,
                "title": "Параметр перешел в критическое состояние",
                "message": f"Параметр '{parameter.name}' оборудования '{equipment.name}' вошел в зону critical.",
            }
        if new_status == METRIC_STATUS_NORMAL and previous_status in {METRIC_STATUS_WARNING, METRIC_STATUS_CRITICAL}:
            return {
                "event_type": EVENT_TYPE_PARAMETER_RECOVERED,
                "severity": METRIC_STATUS_NORMAL,
                "title": "Параметр восстановился",
                "message": f"Параметр '{parameter.name}' оборудования '{equipment.name}' вернулся в норму.",
            }
        return None

    @staticmethod
    def _build_equipment_event(*, equipment, previous_status: str | None, new_status: str):
        if new_status == METRIC_STATUS_WARNING and previous_status != METRIC_STATUS_WARNING:
            return {
                "event_type": EVENT_TYPE_EQUIPMENT_WARNING,
                "severity": METRIC_STATUS_WARNING,
                "title": "Оборудование перешло в warning",
                "message": f"Оборудование '{equipment.name}' перешло в предупредительное состояние.",
            }
        if new_status == METRIC_STATUS_CRITICAL and previous_status != METRIC_STATUS_CRITICAL:
            return {
                "event_type": EVENT_TYPE_EQUIPMENT_CRITICAL,
                "severity": METRIC_STATUS_CRITICAL,
                "title": "Оборудование перешло в critical",
                "message": f"Оборудование '{equipment.name}' перешло в критическое состояние.",
            }
        if new_status == METRIC_STATUS_NORMAL and previous_status in {METRIC_STATUS_WARNING, METRIC_STATUS_CRITICAL}:
            return {
                "event_type": EVENT_TYPE_EQUIPMENT_RECOVERED,
                "severity": METRIC_STATUS_NORMAL,
                "title": "Оборудование восстановилось",
                "message": f"Оборудование '{equipment.name}' вернулось в нормальное состояние.",
            }
        return None
