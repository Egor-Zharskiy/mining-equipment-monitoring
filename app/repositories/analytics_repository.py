from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import (
    Equipment,
    EquipmentState,
    EquipmentType,
    Event,
    MaintenanceTask,
    Notification,
    TelemetryEvaluation,
    TelemetryReading,
)


class AnalyticsRepository:
    """Provides read-only aggregate access for analytics endpoints."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_equipment_status_rows(
        self,
        *,
        equipment_type_id: UUID | None = None,
    ) -> list[tuple[UUID, str, str | None]]:
        query = (
            select(
                EquipmentType.id,
                EquipmentType.name,
                EquipmentState.status,
            )
            .select_from(Equipment)
            .join(EquipmentType, Equipment.equipment_type_id == EquipmentType.id)
            .outerjoin(EquipmentState, EquipmentState.equipment_id == Equipment.id)
        )
        if equipment_type_id is not None:
            query = query.where(Equipment.equipment_type_id == equipment_type_id)

        result = await self._session.execute(query.order_by(EquipmentType.name, Equipment.name))
        return [(row[0], row[1], row[2]) for row in result.all()]

    async def list_event_rows(
        self,
        *,
        equipment_id: UUID | None = None,
        severity: str | None = None,
        event_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[tuple[str, str, datetime]]:
        query = select(Event.severity, Event.event_type, Event.created_at)
        if equipment_id is not None:
            query = query.where(Event.equipment_id == equipment_id)
        if severity is not None:
            query = query.where(Event.severity == severity)
        if event_type is not None:
            query = query.where(Event.event_type == event_type)
        if date_from is not None:
            query = query.where(Event.created_at >= date_from)
        if date_to is not None:
            query = query.where(Event.created_at <= date_to)

        result = await self._session.execute(query.order_by(Event.created_at.asc()))
        return [(row[0], row[1], row[2]) for row in result.all()]

    async def list_telemetry_history(
        self,
        *,
        equipment_id: UUID,
        parameter_id: UUID,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 200,
    ) -> list[TelemetryReading]:
        query: Select[tuple[TelemetryReading]] = (
            select(TelemetryReading)
            .options(
                joinedload(TelemetryReading.equipment).joinedload(Equipment.equipment_type),
                joinedload(TelemetryReading.parameter),
                joinedload(TelemetryReading.evaluation).joinedload(TelemetryEvaluation.threshold_rule),
            )
            .where(
                TelemetryReading.equipment_id == equipment_id,
                TelemetryReading.parameter_id == parameter_id,
            )
        )
        if date_from is not None:
            query = query.where(TelemetryReading.measured_at >= date_from)
        if date_to is not None:
            query = query.where(TelemetryReading.measured_at <= date_to)

        result = await self._session.execute(
            query.order_by(TelemetryReading.measured_at.desc(), TelemetryReading.received_at.desc()).limit(limit)
        )
        return list(result.scalars().unique().all())

    async def list_maintenance_rows(
        self,
        *,
        equipment_id: UUID | None = None,
    ) -> list[tuple[str, str, datetime | None, datetime | None]]:
        query = select(
            MaintenanceTask.status,
            MaintenanceTask.priority,
            MaintenanceTask.due_at,
            MaintenanceTask.completed_at,
        )
        if equipment_id is not None:
            query = query.where(MaintenanceTask.equipment_id == equipment_id)

        result = await self._session.execute(query.order_by(MaintenanceTask.created_at.asc()))
        return [(row[0], row[1], row[2], row[3]) for row in result.all()]

    async def list_notification_rows(
        self,
        *,
        recipient_user_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[tuple[str, str, bool, datetime]]:
        query = select(
            Notification.channel,
            Notification.notification_type,
            Notification.is_read,
            Notification.created_at,
        )
        if recipient_user_id is not None:
            query = query.where(Notification.recipient_user_id == recipient_user_id)
        if date_from is not None:
            query = query.where(Notification.created_at >= date_from)
        if date_to is not None:
            query = query.where(Notification.created_at <= date_to)

        result = await self._session.execute(query.order_by(Notification.created_at.asc()))
        return [(row[0], row[1], row[2], row[3]) for row in result.all()]
