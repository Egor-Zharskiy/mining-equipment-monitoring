from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Equipment, MaintenancePlan, MaintenanceRecord, MaintenanceTask, User


class MaintenanceRecordRepository:
    """Handles database access for maintenance records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        task: MaintenanceTask,
        equipment: Equipment,
        performed_by_user: User,
        summary: str,
        details: str | None,
        performed_at: datetime,
    ) -> MaintenanceRecord:
        record = MaintenanceRecord(
            task=task,
            equipment=equipment,
            performed_by_user=performed_by_user,
            summary=summary,
            details=details,
            performed_at=performed_at,
        )
        self._session.add(record)
        await self._session.flush()
        await self._session.refresh(record)
        return await self.get_by_id(record.id)  # type: ignore[return-value]

    async def get_by_id(self, record_id: UUID) -> MaintenanceRecord | None:
        result = await self._session.execute(
            select(MaintenanceRecord)
            .options(
                joinedload(MaintenanceRecord.task).joinedload(MaintenanceTask.plan).joinedload(MaintenancePlan.equipment_type),
                joinedload(MaintenanceRecord.task).joinedload(MaintenanceTask.plan).joinedload(MaintenancePlan.equipment).joinedload(Equipment.equipment_type),
                joinedload(MaintenanceRecord.task).joinedload(MaintenanceTask.equipment).joinedload(Equipment.equipment_type),
                joinedload(MaintenanceRecord.task).joinedload(MaintenanceTask.created_by_user),
                joinedload(MaintenanceRecord.task).joinedload(MaintenanceTask.assigned_to_user),
                joinedload(MaintenanceRecord.equipment).joinedload(Equipment.equipment_type),
                joinedload(MaintenanceRecord.performed_by_user),
            )
            .where(MaintenanceRecord.id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_by_task_id(self, task_id: UUID) -> MaintenanceRecord | None:
        result = await self._session.execute(
            select(MaintenanceRecord).where(MaintenanceRecord.task_id == task_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        *,
        equipment_id: UUID | None = None,
        task_id: UUID | None = None,
        performed_by_user_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[MaintenanceRecord]:
        query = select(MaintenanceRecord).options(
            joinedload(MaintenanceRecord.task).joinedload(MaintenanceTask.plan).joinedload(MaintenancePlan.equipment_type),
            joinedload(MaintenanceRecord.task).joinedload(MaintenanceTask.plan).joinedload(MaintenancePlan.equipment).joinedload(Equipment.equipment_type),
            joinedload(MaintenanceRecord.task).joinedload(MaintenanceTask.equipment).joinedload(Equipment.equipment_type),
            joinedload(MaintenanceRecord.task).joinedload(MaintenanceTask.created_by_user),
            joinedload(MaintenanceRecord.task).joinedload(MaintenanceTask.assigned_to_user),
            joinedload(MaintenanceRecord.equipment).joinedload(Equipment.equipment_type),
            joinedload(MaintenanceRecord.performed_by_user),
        )
        if equipment_id is not None:
            query = query.where(MaintenanceRecord.equipment_id == equipment_id)
        if task_id is not None:
            query = query.where(MaintenanceRecord.task_id == task_id)
        if performed_by_user_id is not None:
            query = query.where(MaintenanceRecord.performed_by_user_id == performed_by_user_id)
        if date_from is not None:
            query = query.where(MaintenanceRecord.performed_at >= date_from)
        if date_to is not None:
            query = query.where(MaintenanceRecord.performed_at <= date_to)

        result = await self._session.execute(query.order_by(MaintenanceRecord.performed_at.desc()))
        return list(result.scalars().unique().all())
