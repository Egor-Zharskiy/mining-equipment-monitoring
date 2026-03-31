from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import EquipmentType, Parameter, ThresholdRule

UNSET = object()


class ThresholdRuleRepository:
    """Handles database access for threshold rule entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the active asynchronous database session."""

        self._session = session

    async def create(
        self,
        *,
        equipment_type: EquipmentType,
        parameter: Parameter,
        warning_min,
        warning_max,
        critical_min,
        critical_max,
        is_active: bool,
    ) -> ThresholdRule:
        """Persist a new threshold rule."""

        rule = ThresholdRule(
            equipment_type=equipment_type,
            parameter=parameter,
            warning_min=warning_min,
            warning_max=warning_max,
            critical_min=critical_min,
            critical_max=critical_max,
            is_active=is_active,
        )
        self._session.add(rule)
        await self._session.flush()
        await self._session.refresh(rule)
        return await self.get_by_id(rule.id)  # type: ignore[return-value]

    async def get_by_id(self, rule_id: UUID) -> ThresholdRule | None:
        """Return a threshold rule by identifier with related entities loaded."""

        result = await self._session.execute(
            select(ThresholdRule)
            .options(
                selectinload(ThresholdRule.equipment_type),
                selectinload(ThresholdRule.parameter),
            )
            .where(ThresholdRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def get_by_equipment_type_and_parameter(
        self,
        *,
        equipment_type_id: UUID,
        parameter_id: UUID,
    ) -> ThresholdRule | None:
        """Return a threshold rule by its unique equipment type and parameter pair."""

        result = await self._session.execute(
            select(ThresholdRule)
            .options(
                selectinload(ThresholdRule.equipment_type),
                selectinload(ThresholdRule.parameter),
            )
            .where(ThresholdRule.equipment_type_id == equipment_type_id)
            .where(ThresholdRule.parameter_id == parameter_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        *,
        equipment_type_id: UUID | None = None,
        parameter_id: UUID | None = None,
    ) -> list[ThresholdRule]:
        """Return threshold rules optionally filtered by equipment type or parameter."""

        query = select(ThresholdRule).options(
            selectinload(ThresholdRule.equipment_type),
            selectinload(ThresholdRule.parameter),
        )

        if equipment_type_id is not None:
            query = query.where(ThresholdRule.equipment_type_id == equipment_type_id)
        if parameter_id is not None:
            query = query.where(ThresholdRule.parameter_id == parameter_id)

        result = await self._session.execute(query.order_by(ThresholdRule.created_at.desc()))
        return list(result.scalars().all())

    async def update(
        self,
        rule: ThresholdRule,
        *,
        equipment_type: EquipmentType | object = UNSET,
        parameter: Parameter | object = UNSET,
        warning_min=UNSET,
        warning_max=UNSET,
        critical_min=UNSET,
        critical_max=UNSET,
        is_active: bool | object = UNSET,
    ) -> ThresholdRule:
        """Update a threshold rule and return the refreshed entity."""

        if equipment_type is not UNSET:
            rule.equipment_type = equipment_type  # type: ignore[assignment]
        if parameter is not UNSET:
            rule.parameter = parameter  # type: ignore[assignment]
        if warning_min is not UNSET:
            rule.warning_min = warning_min
        if warning_max is not UNSET:
            rule.warning_max = warning_max
        if critical_min is not UNSET:
            rule.critical_min = critical_min
        if critical_max is not UNSET:
            rule.critical_max = critical_max
        if is_active is not UNSET:
            rule.is_active = is_active  # type: ignore[assignment]

        await self._session.flush()
        await self._session.refresh(rule)
        return await self.get_by_id(rule.id)  # type: ignore[return-value]

    async def delete(self, rule: ThresholdRule) -> None:
        """Delete a threshold rule."""

        await self._session.delete(rule)
