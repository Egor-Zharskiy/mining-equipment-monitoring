from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Equipment, Parameter, TelemetryEvaluation, TelemetryReading


class TelemetryReadingRepository:
    """Handles database access for telemetry readings."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the active asynchronous database session."""

        self._session = session

    async def create(
        self,
        *,
        equipment: Equipment,
        parameter: Parameter,
        value,
        measured_at: datetime,
    ) -> TelemetryReading:
        """Persist a new telemetry reading."""

        reading = TelemetryReading(
            equipment=equipment,
            parameter=parameter,
            value=value,
            measured_at=measured_at,
        )
        self._session.add(reading)
        await self._session.flush()
        await self._session.refresh(reading)
        return await self.get_by_id(reading.id)  # type: ignore[return-value]

    async def get_by_id(self, reading_id: UUID) -> TelemetryReading | None:
        """Return a telemetry reading by identifier with related entities loaded."""

        result = await self._session.execute(
            select(TelemetryReading)
            .options(
                joinedload(TelemetryReading.equipment).joinedload(Equipment.equipment_type),
                joinedload(TelemetryReading.parameter),
                joinedload(TelemetryReading.evaluation).joinedload(TelemetryEvaluation.threshold_rule),
            )
            .where(TelemetryReading.id == reading_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        *,
        equipment_id: UUID | None = None,
        parameter_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 100,
    ) -> list[TelemetryReading]:
        """Return telemetry readings filtered by equipment, parameter, or time range."""

        query = select(TelemetryReading).options(
            joinedload(TelemetryReading.equipment).joinedload(Equipment.equipment_type),
            joinedload(TelemetryReading.parameter),
            joinedload(TelemetryReading.evaluation).joinedload(TelemetryEvaluation.threshold_rule),
        )

        if equipment_id is not None:
            query = query.where(TelemetryReading.equipment_id == equipment_id)
        if parameter_id is not None:
            query = query.where(TelemetryReading.parameter_id == parameter_id)
        if date_from is not None:
            query = query.where(TelemetryReading.measured_at >= date_from)
        if date_to is not None:
            query = query.where(TelemetryReading.measured_at <= date_to)

        result = await self._session.execute(
            query.order_by(TelemetryReading.measured_at.desc(), TelemetryReading.received_at.desc()).limit(limit)
        )
        return list(result.scalars().unique().all())
