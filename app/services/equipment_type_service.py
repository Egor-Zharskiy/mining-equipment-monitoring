from uuid import UUID

from app.repositories.equipment_type_repository import EquipmentTypeRepository, UNSET
from app.schemas.equipment_type import EquipmentTypeCreate, EquipmentTypeUpdate


class EquipmentTypeService:
    """Encapsulates business rules for equipment types."""

    def __init__(self, equipment_type_repository: EquipmentTypeRepository) -> None:
        """Store repository dependencies used by the service."""

        self._equipment_type_repository = equipment_type_repository

    async def create_equipment_type(self, payload: EquipmentTypeCreate):
        """Create a new equipment type if its name is unique."""

        existing_type = await self._equipment_type_repository.get_by_name(payload.name)
        if existing_type is not None:
            raise ValueError(f"Equipment type with name '{payload.name}' already exists.")

        return await self._equipment_type_repository.create(
            name=payload.name,
            description=payload.description,
            is_active=payload.is_active,
        )

    async def list_equipment_types(self):
        """Return all equipment types."""

        return await self._equipment_type_repository.list_all()

    async def get_equipment_type(self, equipment_type_id: UUID):
        """Return an equipment type by identifier."""

        return await self._equipment_type_repository.get_by_id(equipment_type_id)

    async def update_equipment_type(self, equipment_type_id: UUID, payload: EquipmentTypeUpdate):
        """Update an existing equipment type."""

        equipment_type = await self._equipment_type_repository.get_by_id(equipment_type_id)
        if equipment_type is None:
            return None

        update_data = payload.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"] != equipment_type.name:
            existing_type = await self._equipment_type_repository.get_by_name(update_data["name"])
            if existing_type is not None:
                raise ValueError(f"Equipment type with name '{update_data['name']}' already exists.")

        return await self._equipment_type_repository.update(
            equipment_type,
            name=update_data["name"] if "name" in update_data else UNSET,
            description=update_data["description"] if "description" in update_data else UNSET,
            is_active=update_data["is_active"] if "is_active" in update_data else UNSET,
        )

    async def delete_equipment_type(self, equipment_type_id: UUID):
        """Delete an equipment type by identifier."""

        equipment_type = await self._equipment_type_repository.get_by_id(equipment_type_id)
        if equipment_type is None:
            return None

        if await self._equipment_type_repository.has_assigned_equipment(equipment_type_id):
            raise ValueError("Equipment type cannot be deleted while assigned equipment exists.")

        await self._equipment_type_repository.delete(equipment_type)
        return equipment_type
