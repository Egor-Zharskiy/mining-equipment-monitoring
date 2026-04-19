from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Equipment, EquipmentType, MaintenancePlan

UNSET = object()


class MaintenancePlanRepository:
    """Handles database access for maintenance plans."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        equipment_type: EquipmentType | None,
        equipment: Equipment | None,
        title: str,
        description: str | None,
        interval_hours: int | None,
        interval_days: int | None,
        is_active: bool,
    ) -> MaintenancePlan:
        plan = MaintenancePlan(
            equipment_type=equipment_type,
            equipment=equipment,
            title=title,
            description=description,
            interval_hours=interval_hours,
            interval_days=interval_days,
            is_active=is_active,
        )
        self._session.add(plan)
        await self._session.flush()
        await self._session.refresh(plan)
        return await self.get_by_id(plan.id)  # type: ignore[return-value]

    async def get_by_id(self, plan_id: UUID) -> MaintenancePlan | None:
        result = await self._session.execute(
            select(MaintenancePlan)
            .options(
                joinedload(MaintenancePlan.equipment_type),
                joinedload(MaintenancePlan.equipment).joinedload(Equipment.equipment_type),
            )
            .where(MaintenancePlan.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        *,
        equipment_type_id: UUID | None = None,
        equipment_id: UUID | None = None,
        is_active: bool | None = None,
    ) -> list[MaintenancePlan]:
        query = select(MaintenancePlan).options(
            joinedload(MaintenancePlan.equipment_type),
            joinedload(MaintenancePlan.equipment).joinedload(Equipment.equipment_type),
        )
        if equipment_type_id is not None:
            query = query.where(MaintenancePlan.equipment_type_id == equipment_type_id)
        if equipment_id is not None:
            query = query.where(MaintenancePlan.equipment_id == equipment_id)
        if is_active is not None:
            query = query.where(MaintenancePlan.is_active == is_active)

        result = await self._session.execute(query.order_by(MaintenancePlan.created_at.desc()))
        return list(result.scalars().all())

    async def update(
        self,
        plan: MaintenancePlan,
        *,
        equipment_type: EquipmentType | None | object = UNSET,
        equipment: Equipment | None | object = UNSET,
        title: str | object = UNSET,
        description: str | None | object = UNSET,
        interval_hours: int | None | object = UNSET,
        interval_days: int | None | object = UNSET,
        is_active: bool | object = UNSET,
    ) -> MaintenancePlan:
        if equipment_type is not UNSET:
            plan.equipment_type = equipment_type  # type: ignore[assignment]
        if equipment is not UNSET:
            plan.equipment = equipment  # type: ignore[assignment]
        if title is not UNSET:
            plan.title = title  # type: ignore[assignment]
        if description is not UNSET:
            plan.description = description  # type: ignore[assignment]
        if interval_hours is not UNSET:
            plan.interval_hours = interval_hours  # type: ignore[assignment]
        if interval_days is not UNSET:
            plan.interval_days = interval_days  # type: ignore[assignment]
        if is_active is not UNSET:
            plan.is_active = is_active  # type: ignore[assignment]

        await self._session.flush()
        await self._session.refresh(plan)
        return await self.get_by_id(plan.id)  # type: ignore[return-value]

    async def delete(self, plan: MaintenancePlan) -> None:
        await self._session.delete(plan)
