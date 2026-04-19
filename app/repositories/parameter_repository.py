from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EquipmentTypeParameter, Parameter

UNSET = object()


class ParameterRepository:
    """Handles database access for monitoring parameter entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the active asynchronous database session."""

        self._session = session

    async def create(
        self,
        *,
        code: str,
        name: str,
        unit: str | None,
        description: str | None,
        is_active: bool,
    ) -> Parameter:
        """Persist a new monitoring parameter."""

        parameter = Parameter(
            code=code,
            name=name,
            unit=unit,
            description=description,
            is_active=is_active,
        )
        self._session.add(parameter)
        await self._session.flush()
        await self._session.refresh(parameter)
        return parameter

    async def get_by_id(self, parameter_id: UUID) -> Parameter | None:
        """Return a parameter by identifier."""

        result = await self._session.execute(select(Parameter).where(Parameter.id == parameter_id))
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Parameter | None:
        """Return a parameter by unique code."""

        result = await self._session.execute(select(Parameter).where(Parameter.code == code))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Parameter]:
        """Return all parameters ordered by name."""

        result = await self._session.execute(select(Parameter).order_by(Parameter.name))
        return list(result.scalars().all())

    async def update(
        self,
        parameter: Parameter,
        *,
        code: str | object = UNSET,
        name: str | object = UNSET,
        unit: str | None | object = UNSET,
        description: str | None | object = UNSET,
        is_active: bool | object = UNSET,
    ) -> Parameter:
        """Update a parameter and return the refreshed entity."""

        if code is not UNSET:
            parameter.code = code  # type: ignore[assignment]
        if name is not UNSET:
            parameter.name = name  # type: ignore[assignment]
        if unit is not UNSET:
            parameter.unit = unit  # type: ignore[assignment]
        if description is not UNSET:
            parameter.description = description  # type: ignore[assignment]
        if is_active is not UNSET:
            parameter.is_active = is_active  # type: ignore[assignment]

        await self._session.flush()
        await self._session.refresh(parameter)
        return parameter

    async def delete(self, parameter: Parameter) -> None:
        """Delete a parameter."""

        await self._session.delete(parameter)

    async def has_bindings(self, parameter_id: UUID) -> bool:
        """Return whether the parameter is assigned to any equipment type."""

        result = await self._session.execute(
            select(EquipmentTypeParameter.id)
            .where(EquipmentTypeParameter.parameter_id == parameter_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
