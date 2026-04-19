from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import EquipmentParameterState


class EquipmentParameterStateRepository:
    """Handles database access for per-parameter equipment state snapshots."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the active asynchronous database session."""

        self._session = session

    async def get_by_equipment_and_parameter(
        self,
        *,
        equipment_id: UUID,
        parameter_id: UUID,
    ) -> EquipmentParameterState | None:
        """Return the latest parameter state snapshot for an equipment and parameter pair."""

        result = await self._session.execute(
            select(EquipmentParameterState)
            .options(joinedload(EquipmentParameterState.parameter))
            .where(EquipmentParameterState.equipment_id == equipment_id)
            .where(EquipmentParameterState.parameter_id == parameter_id)
        )
        return result.scalar_one_or_none()

    async def list_by_equipment(self, equipment_id: UUID) -> list[EquipmentParameterState]:
        """Return all parameter state snapshots for an equipment unit."""

        result = await self._session.execute(
            select(EquipmentParameterState)
            .options(joinedload(EquipmentParameterState.parameter))
            .where(EquipmentParameterState.equipment_id == equipment_id)
            .order_by(EquipmentParameterState.measured_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        equipment,
        parameter,
        latest_telemetry_reading,
        threshold_rule,
        value,
        status: str,
        measured_at,
    ) -> EquipmentParameterState:
        """Persist a new parameter state snapshot."""

        state = EquipmentParameterState(
            equipment=equipment,
            parameter=parameter,
            latest_telemetry_reading=latest_telemetry_reading,
            threshold_rule=threshold_rule,
            value=value,
            status=status,
            measured_at=measured_at,
        )
        self._session.add(state)
        await self._session.flush()
        await self._session.refresh(state)
        return await self.get_by_equipment_and_parameter(
            equipment_id=state.equipment_id,
            parameter_id=state.parameter_id,
        )  # type: ignore[return-value]

    async def update(
        self,
        state: EquipmentParameterState,
        *,
        latest_telemetry_reading,
        threshold_rule,
        value,
        status: str,
        measured_at,
    ) -> EquipmentParameterState:
        """Update the latest parameter state snapshot."""

        state.latest_telemetry_reading = latest_telemetry_reading
        state.threshold_rule = threshold_rule
        state.value = value
        state.status = status
        state.measured_at = measured_at

        await self._session.flush()
        await self._session.refresh(state)
        return await self.get_by_equipment_and_parameter(
            equipment_id=state.equipment_id,
            parameter_id=state.parameter_id,
        )  # type: ignore[return-value]
