from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Equipment, EquipmentState


class EquipmentStateRepository:
    """Handles database access for aggregated equipment state snapshots."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the active asynchronous database session."""

        self._session = session

    async def get_by_equipment_id(self, equipment_id: UUID) -> EquipmentState | None:
        """Return the current state snapshot of an equipment unit."""

        result = await self._session.execute(
            select(EquipmentState)
            .options(joinedload(EquipmentState.equipment).joinedload(Equipment.equipment_type))
            .where(EquipmentState.equipment_id == equipment_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, *, status: str | None = None) -> list[EquipmentState]:
        """Return all equipment state snapshots optionally filtered by status."""

        query = select(EquipmentState).options(
            joinedload(EquipmentState.equipment).joinedload(Equipment.equipment_type)
        )
        if status is not None:
            query = query.where(EquipmentState.status == status)

        result = await self._session.execute(query.order_by(EquipmentState.updated_at.desc()))
        return list(result.scalars().all())

    async def create(
        self,
        *,
        equipment,
        status: str,
        warning_count: int,
        critical_count: int,
        last_evaluated_at,
    ) -> EquipmentState:
        """Persist a new aggregated equipment state snapshot."""

        state = EquipmentState(
            equipment=equipment,
            status=status,
            warning_count=warning_count,
            critical_count=critical_count,
            last_evaluated_at=last_evaluated_at,
        )
        self._session.add(state)
        await self._session.flush()
        await self._session.refresh(state)
        return await self.get_by_equipment_id(state.equipment_id)  # type: ignore[return-value]

    async def update(
        self,
        state: EquipmentState,
        *,
        status: str,
        warning_count: int,
        critical_count: int,
        last_evaluated_at,
    ) -> EquipmentState:
        """Update an aggregated equipment state snapshot."""

        state.status = status
        state.warning_count = warning_count
        state.critical_count = critical_count
        state.last_evaluated_at = last_evaluated_at

        await self._session.flush()
        await self._session.refresh(state)
        return await self.get_by_equipment_id(state.equipment_id)  # type: ignore[return-value]
