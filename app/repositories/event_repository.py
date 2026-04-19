from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Equipment, Event


class EventRepository:
    """Handles database access for monitoring events."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the active asynchronous database session."""

        self._session = session

    async def create(
        self,
        *,
        equipment,
        parameter,
        telemetry_reading,
        event_type: str,
        severity: str,
        title: str,
        message: str,
    ) -> Event:
        """Persist a new monitoring event."""

        event = Event(
            equipment=equipment,
            parameter=parameter,
            telemetry_reading=telemetry_reading,
            event_type=event_type,
            severity=severity,
            title=title,
            message=message,
        )
        self._session.add(event)
        await self._session.flush()
        await self._session.refresh(event)
        return await self.get_by_id(event.id)  # type: ignore[return-value]

    async def get_by_id(self, event_id: UUID) -> Event | None:
        """Return an event by identifier with related entities loaded."""

        result = await self._session.execute(
            select(Event)
            .options(
                joinedload(Event.equipment).joinedload(Equipment.equipment_type),
                joinedload(Event.parameter),
                joinedload(Event.telemetry_reading),
            )
            .where(Event.id == event_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        *,
        equipment_id: UUID | None = None,
        parameter_id: UUID | None = None,
        severity: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """Return monitoring events optionally filtered by equipment, parameter, severity, or type."""

        query = select(Event).options(
            joinedload(Event.equipment).joinedload(Equipment.equipment_type),
            joinedload(Event.parameter),
            joinedload(Event.telemetry_reading),
        )

        if equipment_id is not None:
            query = query.where(Event.equipment_id == equipment_id)
        if parameter_id is not None:
            query = query.where(Event.parameter_id == parameter_id)
        if severity is not None:
            query = query.where(Event.severity == severity)
        if event_type is not None:
            query = query.where(Event.event_type == event_type)

        result = await self._session.execute(query.order_by(Event.created_at.desc()).limit(limit))
        return list(result.scalars().unique().all())
