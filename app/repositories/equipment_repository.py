from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Equipment, EquipmentType

UNSET = object()


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
            .options(joinedload(Equipment.equipment_type))
            .where(Equipment.id == equipment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Equipment | None:
        """Return equipment by unique code."""

        result = await self._session.execute(
            select(Equipment)
            .options(joinedload(Equipment.equipment_type))
            .where(Equipment.code == code)
        )
        return result.scalar_one_or_none()

    async def get_by_serial_number(self, serial_number: str) -> Equipment | None:
        """Return equipment by serial number."""

        result = await self._session.execute(
            select(Equipment)
            .options(joinedload(Equipment.equipment_type))
            .where(Equipment.serial_number == serial_number)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Equipment]:
        """Return all equipment ordered by name."""

        result = await self._session.execute(
            select(Equipment)
            .options(joinedload(Equipment.equipment_type))
            .order_by(Equipment.name)
        )
        return list(result.scalars().all())

    async def update(
        self,
        equipment: Equipment,
        *,
        name: str | object = UNSET,
        code: str | object = UNSET,
        serial_number: str | None | object = UNSET,
        equipment_type: EquipmentType | object = UNSET,
        location: str | object = UNSET,
        description: str | None | object = UNSET,
        specifications: dict | None | object = UNSET,
        is_active: bool | object = UNSET,
    ) -> Equipment:
        """Update equipment and return the refreshed entity."""

        if name is not UNSET:
            equipment.name = name  # type: ignore[assignment]
        if code is not UNSET:
            equipment.code = code  # type: ignore[assignment]
        if serial_number is not UNSET:
            equipment.serial_number = serial_number  # type: ignore[assignment]
        if equipment_type is not UNSET:
            equipment.equipment_type = equipment_type  # type: ignore[assignment]
        if location is not UNSET:
            equipment.location = location  # type: ignore[assignment]
        if description is not UNSET:
            equipment.description = description  # type: ignore[assignment]
        if specifications is not UNSET:
            equipment.specifications = specifications  # type: ignore[assignment]
        if is_active is not UNSET:
            equipment.is_active = is_active  # type: ignore[assignment]

        await self._session.flush()
        await self._session.refresh(equipment)
        return await self.get_by_id(equipment.id)

    async def delete(self, equipment: Equipment) -> None:
        """Delete equipment."""

        await self._session.delete(equipment)
