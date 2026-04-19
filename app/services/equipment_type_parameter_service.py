from uuid import UUID

from app.repositories.equipment_type_parameter_repository import EquipmentTypeParameterRepository
from app.repositories.equipment_type_repository import EquipmentTypeRepository
from app.repositories.parameter_repository import ParameterRepository
from app.schemas.equipment_type_parameter import EquipmentTypeParameterCreate


class EquipmentTypeParameterService:
    """Encapsulates business rules for equipment type parameter bindings."""

    def __init__(
        self,
        equipment_type_parameter_repository: EquipmentTypeParameterRepository,
        equipment_type_repository: EquipmentTypeRepository,
        parameter_repository: ParameterRepository,
    ) -> None:
        """Store repository dependencies used by the service."""

        self._equipment_type_parameter_repository = equipment_type_parameter_repository
        self._equipment_type_repository = equipment_type_repository
        self._parameter_repository = parameter_repository

    async def create_binding(self, payload: EquipmentTypeParameterCreate):
        """Create a new binding between an equipment type and a parameter."""

        equipment_type = await self._equipment_type_repository.get_by_id(payload.equipment_type_id)
        if equipment_type is None:
            raise ValueError("Equipment type was not found.")

        parameter = await self._parameter_repository.get_by_id(payload.parameter_id)
        if parameter is None:
            raise ValueError("Parameter was not found.")

        existing_binding = await self._equipment_type_parameter_repository.get_by_equipment_type_and_parameter(
            equipment_type_id=payload.equipment_type_id,
            parameter_id=payload.parameter_id,
        )
        if existing_binding is not None:
            raise ValueError("Parameter is already assigned to this equipment type.")

        return await self._equipment_type_parameter_repository.create(
            equipment_type=equipment_type,
            parameter=parameter,
            is_required=payload.is_required,
        )

    async def list_bindings(
        self,
        *,
        equipment_type_id: UUID | None = None,
        parameter_id: UUID | None = None,
    ):
        """Return equipment type parameter bindings with optional filtering."""

        return await self._equipment_type_parameter_repository.list_all(
            equipment_type_id=equipment_type_id,
            parameter_id=parameter_id,
        )

    async def get_binding(self, binding_id: UUID):
        """Return a binding by identifier."""

        return await self._equipment_type_parameter_repository.get_by_id(binding_id)

    async def delete_binding(self, binding_id: UUID):
        """Delete a binding by identifier."""

        binding = await self._equipment_type_parameter_repository.get_by_id(binding_id)
        if binding is None:
            return None

        await self._equipment_type_parameter_repository.delete(binding)
        return binding
