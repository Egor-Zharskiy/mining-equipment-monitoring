from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Equipment, EquipmentType


class EquipmentRepository:
    """Handles database access for equipment entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the active asynchronous database session."""

        self._session = session

    async def create(
        self,
        *,
        name: str,
        code: str,
        serial_number: str | None,
        equipment_type: EquipmentType,
        location: str,
        description: str | None,
        specifications: dict | None,
        is_active: bool,
    ) -> Equipment:
        """Persist a new equipment unit."""

        equipment = Equipment(
            name=name,
            code=code,
            serial_number=serial_number,
            equipment_type=equipment_type,
            location=location,
            description=description,
            specifications=specifications,
            is_active=is_active,
        )
        self._session.add(equipment)
        await self._session.flush()
        await self._session.refresh(equipment)
        return await self.get_by_id(equipment.id)

    async def get_by_id(self, equipment_id: UUID) -> Equipment | None:
        """Return equipment by identifier with eager-loaded type."""

        result = await self._session.execute(
            select(Equipment)
            .options(selectinload(Equipment.equipment_type))
            .where(Equipment.id == equipment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Equipment | None:
        """Return equipment by unique code."""

        result = await self._session.execute(
            select(Equipment)
            .options(selectinload(Equipment.equipment_type))
            .where(Equipment.code == code)
        )
        return result.scalar_one_or_none()

    async def get_by_serial_number(self, serial_number: str) -> Equipment | None:
        """Return equipment by serial number."""

        result = await self._session.execute(
            select(Equipment)
            .options(selectinload(Equipment.equipment_type))
            .where(Equipment.serial_number == serial_number)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Equipment]:
        """Return all equipment ordered by name."""

        result = await self._session.execute(
            select(Equipment)
            .options(selectinload(Equipment.equipment_type))
            .order_by(Equipment.name)
        )
        return list(result.scalars().all())

    async def update(
        self,
        equipment: Equipment,
        *,
        name: str | None = None,
        code: str | None = None,
        serial_number: str | None = None,
        equipment_type: EquipmentType | None = None,
        location: str | None = None,
        description: str | None = None,
        specifications: dict | None = None,
        is_active: bool | None = None,
    ) -> Equipment:
        """Update equipment and return the refreshed entity."""

        if name is not None:
            equipment.name = name
        if code is not None:
            equipment.code = code
        if serial_number is not None:
            equipment.serial_number = serial_number
        if equipment_type is not None:
            equipment.equipment_type = equipment_type
        if location is not None:
            equipment.location = location
        if description is not None:
            equipment.description = description
        if specifications is not None:
            equipment.specifications = specifications
        if is_active is not None:
            equipment.is_active = is_active

        await self._session.flush()
        await self._session.refresh(equipment)
        return await self.get_by_id(equipment.id)

    async def delete(self, equipment: Equipment) -> None:
        """Delete equipment."""

        await self._session.delete(equipment)
