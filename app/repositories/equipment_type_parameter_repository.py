from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import EquipmentType, EquipmentTypeParameter, Parameter


class EquipmentTypeParameterRepository:
    """Handles database access for equipment type parameter bindings."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the active asynchronous database session."""

        self._session = session

    async def create(
        self,
        *,
        equipment_type: EquipmentType,
        parameter: Parameter,
        is_required: bool,
    ) -> EquipmentTypeParameter:
        """Persist a new equipment type parameter binding."""

        binding = EquipmentTypeParameter(
            equipment_type=equipment_type,
            parameter=parameter,
            is_required=is_required,
        )
        self._session.add(binding)
        await self._session.flush()
        await self._session.refresh(binding)
        return await self.get_by_id(binding.id)  # type: ignore[return-value]

    async def get_by_id(self, binding_id: UUID) -> EquipmentTypeParameter | None:
        """Return a binding by identifier with related entities loaded."""

        result = await self._session.execute(
            select(EquipmentTypeParameter)
            .options(
                selectinload(EquipmentTypeParameter.equipment_type),
                selectinload(EquipmentTypeParameter.parameter),
            )
            .where(EquipmentTypeParameter.id == binding_id)
        )
        return result.scalar_one_or_none()

    async def get_by_equipment_type_and_parameter(
        self,
        *,
        equipment_type_id: UUID,
        parameter_id: UUID,
    ) -> EquipmentTypeParameter | None:
        """Return a binding by its unique equipment type and parameter pair."""

        result = await self._session.execute(
            select(EquipmentTypeParameter)
            .options(
                selectinload(EquipmentTypeParameter.equipment_type),
                selectinload(EquipmentTypeParameter.parameter),
            )
            .where(EquipmentTypeParameter.equipment_type_id == equipment_type_id)
            .where(EquipmentTypeParameter.parameter_id == parameter_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        *,
        equipment_type_id: UUID | None = None,
        parameter_id: UUID | None = None,
    ) -> list[EquipmentTypeParameter]:
        """Return bindings filtered by equipment type or parameter if requested."""

        query = select(EquipmentTypeParameter).options(
            selectinload(EquipmentTypeParameter.equipment_type),
            selectinload(EquipmentTypeParameter.parameter),
        )

        if equipment_type_id is not None:
            query = query.where(EquipmentTypeParameter.equipment_type_id == equipment_type_id)
        if parameter_id is not None:
            query = query.where(EquipmentTypeParameter.parameter_id == parameter_id)

        result = await self._session.execute(query.order_by(EquipmentTypeParameter.created_at.desc()))
        return list(result.scalars().all())

    async def delete(self, binding: EquipmentTypeParameter) -> None:
        """Delete a binding."""

        await self._session.delete(binding)
