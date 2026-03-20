from uuid import UUID

from app.repositories.equipment_repository import EquipmentRepository
from app.repositories.equipment_type_repository import EquipmentTypeRepository
from app.schemas.equipment import EquipmentCreate, EquipmentUpdate


class EquipmentService:
    """Encapsulates business rules for equipment units."""

    def __init__(
        self,
        equipment_repository: EquipmentRepository,
        equipment_type_repository: EquipmentTypeRepository,
    ) -> None:
        """Store repository dependencies used by the service."""

        self._equipment_repository = equipment_repository
        self._equipment_type_repository = equipment_type_repository

    async def create_equipment(self, payload: EquipmentCreate):
        """Create a new equipment unit if identifiers are unique."""

        existing_code = await self._equipment_repository.get_by_code(payload.code)
        if existing_code is not None:
            raise ValueError(f"Equipment with code '{payload.code}' already exists.")

        if payload.serial_number is not None:
            existing_serial_number = await self._equipment_repository.get_by_serial_number(payload.serial_number)
            if existing_serial_number is not None:
                raise ValueError(f"Equipment with serial number '{payload.serial_number}' already exists.")

        equipment_type = await self._equipment_type_repository.get_by_id(payload.equipment_type_id)
        if equipment_type is None:
            raise ValueError("Equipment type was not found.")

        return await self._equipment_repository.create(
            name=payload.name,
            code=payload.code,
            serial_number=payload.serial_number,
            equipment_type=equipment_type,
            location=payload.location,
            description=payload.description,
            specifications=payload.specifications,
            is_active=payload.is_active,
        )

    async def list_equipment(self):
        """Return all equipment units."""

        return await self._equipment_repository.list_all()

    async def get_equipment(self, equipment_id: UUID):
        """Return equipment by identifier."""

        return await self._equipment_repository.get_by_id(equipment_id)

    async def update_equipment(self, equipment_id: UUID, payload: EquipmentUpdate):
        """Update an existing equipment unit."""

        equipment = await self._equipment_repository.get_by_id(equipment_id)
        if equipment is None:
            return None

        if payload.code is not None and payload.code != equipment.code:
            existing_code = await self._equipment_repository.get_by_code(payload.code)
            if existing_code is not None:
                raise ValueError(f"Equipment with code '{payload.code}' already exists.")

        if payload.serial_number is not None and payload.serial_number != equipment.serial_number:
            existing_serial_number = await self._equipment_repository.get_by_serial_number(payload.serial_number)
            if existing_serial_number is not None:
                raise ValueError(f"Equipment with serial number '{payload.serial_number}' already exists.")

        equipment_type = None
        if payload.equipment_type_id is not None:
            equipment_type = await self._equipment_type_repository.get_by_id(payload.equipment_type_id)
            if equipment_type is None:
                raise ValueError("Equipment type was not found.")

        return await self._equipment_repository.update(
            equipment,
            name=payload.name,
            code=payload.code,
            serial_number=payload.serial_number,
            equipment_type=equipment_type,
            location=payload.location,
            description=payload.description,
            specifications=payload.specifications,
            is_active=payload.is_active,
        )

    async def delete_equipment(self, equipment_id: UUID):
        """Delete an equipment unit by identifier."""

        equipment = await self._equipment_repository.get_by_id(equipment_id)
        if equipment is None:
            return None

        await self._equipment_repository.delete(equipment)
        return equipment
