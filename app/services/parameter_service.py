from uuid import UUID

from app.repositories.parameter_repository import ParameterRepository, UNSET
from app.schemas.parameter import ParameterCreate, ParameterUpdate


class ParameterService:
    """Encapsulates business rules for monitoring parameters."""

    def __init__(self, parameter_repository: ParameterRepository) -> None:
        """Store repository dependencies used by the service."""

        self._parameter_repository = parameter_repository

    async def create_parameter(self, payload: ParameterCreate):
        """Create a new parameter if its code is unique."""

        existing_parameter = await self._parameter_repository.get_by_code(payload.code)
        if existing_parameter is not None:
            raise ValueError(f"Parameter with code '{payload.code}' already exists.")

        return await self._parameter_repository.create(
            code=payload.code,
            name=payload.name,
            unit=payload.unit,
            description=payload.description,
            is_active=payload.is_active,
        )

    async def list_parameters(self):
        """Return all monitoring parameters."""

        return await self._parameter_repository.list_all()

    async def get_parameter(self, parameter_id: UUID):
        """Return a parameter by identifier."""

        return await self._parameter_repository.get_by_id(parameter_id)

    async def update_parameter(self, parameter_id: UUID, payload: ParameterUpdate):
        """Update an existing monitoring parameter."""

        parameter = await self._parameter_repository.get_by_id(parameter_id)
        if parameter is None:
            return None

        update_data = payload.model_dump(exclude_unset=True)

        if "code" in update_data and update_data["code"] != parameter.code:
            existing_parameter = await self._parameter_repository.get_by_code(update_data["code"])
            if existing_parameter is not None:
                raise ValueError(f"Parameter with code '{update_data['code']}' already exists.")

        return await self._parameter_repository.update(
            parameter,
            code=update_data["code"] if "code" in update_data else UNSET,
            name=update_data["name"] if "name" in update_data else UNSET,
            unit=update_data["unit"] if "unit" in update_data else UNSET,
            description=update_data["description"] if "description" in update_data else UNSET,
            is_active=update_data["is_active"] if "is_active" in update_data else UNSET,
        )

    async def delete_parameter(self, parameter_id: UUID):
        """Delete a parameter when it has no equipment type bindings."""

        parameter = await self._parameter_repository.get_by_id(parameter_id)
        if parameter is None:
            return None

        if await self._parameter_repository.has_bindings(parameter_id):
            raise ValueError("Parameter cannot be deleted while assigned to equipment types.")

        await self._parameter_repository.delete(parameter)
        return parameter
