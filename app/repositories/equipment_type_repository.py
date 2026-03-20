from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Equipment, EquipmentType


class EquipmentTypeRepository:
    """Handles database access for equipment type entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the active asynchronous database session."""

        self._session = session

    async def create(self, *, name: str, description: str | None, is_active: bool) -> EquipmentType:
        """Persist a new equipment type."""

        equipment_type = EquipmentType(name=name, description=description, is_active=is_active)
        self._session.add(equipment_type)
        await self._session.flush()
        await self._session.refresh(equipment_type)
        return equipment_type

    async def get_by_id(self, equipment_type_id: UUID) -> EquipmentType | None:
        """Return an equipment type by identifier."""

        result = await self._session.execute(
            select(EquipmentType).where(EquipmentType.id == equipment_type_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> EquipmentType | None:
        """Return an equipment type by its unique name."""

        result = await self._session.execute(
            select(EquipmentType).where(EquipmentType.name == name)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[EquipmentType]:
        """Return all equipment types ordered by name."""

        result = await self._session.execute(
            select(EquipmentType).order_by(EquipmentType.name)
        )
        return list(result.scalars().all())

    async def update(
        self,
        equipment_type: EquipmentType,
        *,
        name: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> EquipmentType:
        """Update an equipment type and return the refreshed entity."""

        if name is not None:
            equipment_type.name = name
        if description is not None:
            equipment_type.description = description
        if is_active is not None:
            equipment_type.is_active = is_active

        await self._session.flush()
        await self._session.refresh(equipment_type)
        return equipment_type

    async def delete(self, equipment_type: EquipmentType) -> None:
        """Delete an equipment type."""

        await self._session.delete(equipment_type)

    async def has_assigned_equipment(self, equipment_type_id: UUID) -> bool:
        """Return whether any equipment units are assigned to the type."""

        result = await self._session.execute(
            select(Equipment.id).where(Equipment.equipment_type_id == equipment_type_id).limit(1)
        )
        return result.scalar_one_or_none() is not None
