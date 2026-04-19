from uuid import UUID

from app.repositories.equipment_repository import EquipmentRepository
from app.repositories.equipment_type_repository import EquipmentTypeRepository
from app.repositories.maintenance_plan_repository import MaintenancePlanRepository, UNSET
from app.schemas.maintenance import MaintenancePlanCreate, MaintenancePlanUpdate


class MaintenancePlanService:
    """Encapsulates business rules for maintenance plans."""

    def __init__(
        self,
        maintenance_plan_repository: MaintenancePlanRepository,
        equipment_repository: EquipmentRepository,
        equipment_type_repository: EquipmentTypeRepository,
    ) -> None:
        self._maintenance_plan_repository = maintenance_plan_repository
        self._equipment_repository = equipment_repository
        self._equipment_type_repository = equipment_type_repository

    async def create_plan(self, payload: MaintenancePlanCreate):
        target = await self._resolve_target(
            equipment_type_id=payload.equipment_type_id,
            equipment_id=payload.equipment_id,
        )
        self._validate_intervals(payload.interval_hours, payload.interval_days)

        return await self._maintenance_plan_repository.create(
            equipment_type=target["equipment_type"],
            equipment=target["equipment"],
            title=payload.title,
            description=payload.description,
            interval_hours=payload.interval_hours,
            interval_days=payload.interval_days,
            is_active=payload.is_active,
        )

    async def list_plans(
        self,
        *,
        equipment_type_id: UUID | None = None,
        equipment_id: UUID | None = None,
        is_active: bool | None = None,
    ):
        return await self._maintenance_plan_repository.list_all(
            equipment_type_id=equipment_type_id,
            equipment_id=equipment_id,
            is_active=is_active,
        )

    async def get_plan(self, plan_id: UUID):
        return await self._maintenance_plan_repository.get_by_id(plan_id)

    async def update_plan(self, plan_id: UUID, payload: MaintenancePlanUpdate):
        plan = await self._maintenance_plan_repository.get_by_id(plan_id)
        if plan is None:
            return None

        update_data = payload.model_dump(exclude_unset=True)

        final_equipment_type_id = (
            update_data["equipment_type_id"] if "equipment_type_id" in update_data else plan.equipment_type_id
        )
        final_equipment_id = update_data["equipment_id"] if "equipment_id" in update_data else plan.equipment_id
        final_interval_hours = update_data["interval_hours"] if "interval_hours" in update_data else plan.interval_hours
        final_interval_days = update_data["interval_days"] if "interval_days" in update_data else plan.interval_days

        target = await self._resolve_target(
            equipment_type_id=final_equipment_type_id,
            equipment_id=final_equipment_id,
        )
        self._validate_intervals(final_interval_hours, final_interval_days)

        return await self._maintenance_plan_repository.update(
            plan,
            equipment_type=target["equipment_type"] if "equipment_type_id" in update_data or "equipment_id" in update_data else UNSET,
            equipment=target["equipment"] if "equipment_type_id" in update_data or "equipment_id" in update_data else UNSET,
            title=update_data["title"] if "title" in update_data else UNSET,
            description=update_data["description"] if "description" in update_data else UNSET,
            interval_hours=update_data["interval_hours"] if "interval_hours" in update_data else UNSET,
            interval_days=update_data["interval_days"] if "interval_days" in update_data else UNSET,
            is_active=update_data["is_active"] if "is_active" in update_data else UNSET,
        )

    async def delete_plan(self, plan_id: UUID):
        plan = await self._maintenance_plan_repository.get_by_id(plan_id)
        if plan is None:
            return None

        await self._maintenance_plan_repository.delete(plan)
        return plan

    async def _resolve_target(
        self,
        *,
        equipment_type_id: UUID | None,
        equipment_id: UUID | None,
    ) -> dict[str, object | None]:
        if (equipment_type_id is None and equipment_id is None) or (
            equipment_type_id is not None and equipment_id is not None
        ):
            raise ValueError("Maintenance plan must target exactly one entity: equipment_type_id or equipment_id.")

        equipment_type = None
        equipment = None

        if equipment_type_id is not None:
            equipment_type = await self._equipment_type_repository.get_by_id(equipment_type_id)
            if equipment_type is None:
                raise ValueError("Equipment type was not found.")

        if equipment_id is not None:
            equipment = await self._equipment_repository.get_by_id(equipment_id)
            if equipment is None:
                raise ValueError("Equipment was not found.")

        return {"equipment_type": equipment_type, "equipment": equipment}

    @staticmethod
    def _validate_intervals(interval_hours: int | None, interval_days: int | None) -> None:
        if interval_hours is None and interval_days is None:
            raise ValueError("Maintenance plan requires interval_hours or interval_days.")
