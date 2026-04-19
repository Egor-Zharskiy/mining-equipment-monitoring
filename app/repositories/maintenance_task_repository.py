from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Equipment, MaintenancePlan, MaintenanceTask, User

UNSET = object()


class MaintenanceTaskRepository:
    """Handles database access for maintenance tasks."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        plan: MaintenancePlan | None,
        equipment: Equipment,
        status: str,
        priority: str,
        title: str,
        description: str | None,
        due_at,
        created_by_user: User | None,
        assigned_to_user: User | None,
    ) -> MaintenanceTask:
        task = MaintenanceTask(
            plan=plan,
            equipment=equipment,
            status=status,
            priority=priority,
            title=title,
            description=description,
            due_at=due_at,
            created_by_user=created_by_user,
            assigned_to_user=assigned_to_user,
        )
        self._session.add(task)
        await self._session.flush()
        await self._session.refresh(task)
        return await self.get_by_id(task.id)  # type: ignore[return-value]

    async def get_by_id(self, task_id: UUID) -> MaintenanceTask | None:
        result = await self._session.execute(
            select(MaintenanceTask)
            .options(
                joinedload(MaintenanceTask.plan).joinedload(MaintenancePlan.equipment_type),
                joinedload(MaintenanceTask.plan).joinedload(MaintenancePlan.equipment).joinedload(Equipment.equipment_type),
                joinedload(MaintenanceTask.equipment).joinedload(Equipment.equipment_type),
                joinedload(MaintenanceTask.created_by_user),
                joinedload(MaintenanceTask.assigned_to_user),
            )
            .where(MaintenanceTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        *,
        equipment_id: UUID | None = None,
        status: str | None = None,
        priority: str | None = None,
        assigned_to_user_id: UUID | None = None,
    ) -> list[MaintenanceTask]:
        query = select(MaintenanceTask).options(
            joinedload(MaintenanceTask.plan).joinedload(MaintenancePlan.equipment_type),
            joinedload(MaintenanceTask.plan).joinedload(MaintenancePlan.equipment).joinedload(Equipment.equipment_type),
            joinedload(MaintenanceTask.equipment).joinedload(Equipment.equipment_type),
            joinedload(MaintenanceTask.created_by_user),
            joinedload(MaintenanceTask.assigned_to_user),
        )
        if equipment_id is not None:
            query = query.where(MaintenanceTask.equipment_id == equipment_id)
        if status is not None:
            query = query.where(MaintenanceTask.status == status)
        if priority is not None:
            query = query.where(MaintenanceTask.priority == priority)
        if assigned_to_user_id is not None:
            query = query.where(MaintenanceTask.assigned_to_user_id == assigned_to_user_id)

        result = await self._session.execute(
            query.order_by(MaintenanceTask.created_at.desc(), MaintenanceTask.updated_at.desc())
        )
        return list(result.scalars().unique().all())

    async def update(
        self,
        task: MaintenanceTask,
        *,
        status: str | object = UNSET,
        priority: str | object = UNSET,
        title: str | object = UNSET,
        description: str | None | object = UNSET,
        due_at=UNSET,
        assigned_to_user: User | None | object = UNSET,
        completed_at=UNSET,
    ) -> MaintenanceTask:
        if status is not UNSET:
            task.status = status  # type: ignore[assignment]
        if priority is not UNSET:
            task.priority = priority  # type: ignore[assignment]
        if title is not UNSET:
            task.title = title  # type: ignore[assignment]
        if description is not UNSET:
            task.description = description  # type: ignore[assignment]
        if due_at is not UNSET:
            task.due_at = due_at
        if assigned_to_user is not UNSET:
            task.assigned_to_user = assigned_to_user  # type: ignore[assignment]
        if completed_at is not UNSET:
            task.completed_at = completed_at

        await self._session.flush()
        await self._session.refresh(task)
        return await self.get_by_id(task.id)  # type: ignore[return-value]
