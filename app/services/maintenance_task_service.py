
from app.core.maintenance import (
    MAINTENANCE_TASK_STATUS_CANCELLED,
    MAINTENANCE_TASK_STATUS_DONE,
    MAINTENANCE_TASK_STATUS_IN_PROGRESS,
    MAINTENANCE_TASK_STATUS_OPEN,
    VALID_MAINTENANCE_TASK_PRIORITIES,
    VALID_MAINTENANCE_TASK_STATUSES,
)
from app.repositories.equipment_repository import EquipmentRepository
from app.repositories.maintenance_plan_repository import MaintenancePlanRepository
from app.repositories.maintenance_record_repository import MaintenanceRecordRepository
from app.repositories.maintenance_task_repository import MaintenanceTaskRepository, UNSET
from app.repositories.user_repository import UserRepository
from app.schemas.maintenance import MaintenanceTaskComplete, MaintenanceTaskCreate, MaintenanceTaskUpdate
from app.services.notification_service import NotificationService


class MaintenanceTaskService:
    """Encapsulates business rules for maintenance tasks and completion records."""

    def __init__(
        self,
        maintenance_task_repository: MaintenanceTaskRepository,
        maintenance_plan_repository: MaintenancePlanRepository,
        maintenance_record_repository: MaintenanceRecordRepository,
        equipment_repository: EquipmentRepository,
        user_repository: UserRepository,
        notification_service: NotificationService | None = None,
    ) -> None:
        self._maintenance_task_repository = maintenance_task_repository
        self._maintenance_plan_repository = maintenance_plan_repository
        self._maintenance_record_repository = maintenance_record_repository
        self._equipment_repository = equipment_repository
        self._user_repository = user_repository
        self._notification_service = notification_service

    async def create_task(self, payload: MaintenanceTaskCreate, *, actor_user_id):
        equipment = await self._equipment_repository.get_by_id(payload.equipment_id)
        if equipment is None:
            raise ValueError("Equipment was not found.")

        plan = None
        if payload.plan_id is not None:
            plan = await self._maintenance_plan_repository.get_by_id(payload.plan_id)
            if plan is None:
                raise ValueError("Maintenance plan was not found.")
            if not plan.is_active:
                raise ValueError("Inactive maintenance plan cannot be used to create tasks.")
            self._validate_plan_compatibility(plan, equipment)

        created_by_user = await self._user_repository.get_by_id(actor_user_id)
        assigned_to_user = None
        if payload.assigned_to_user_id is not None:
            assigned_to_user = await self._user_repository.get_by_id(payload.assigned_to_user_id)
            if assigned_to_user is None:
                raise ValueError("Assigned user was not found.")

        priority = self._validate_priority(payload.priority)

        title = payload.title or (plan.title if plan is not None else None)
        if title is None:
            raise ValueError("Maintenance task title is required when plan_id is not provided.")

        description = payload.description if payload.description is not None else (plan.description if plan is not None else None)

        task = await self._maintenance_task_repository.create(
            plan=plan,
            equipment=equipment,
            status=MAINTENANCE_TASK_STATUS_OPEN,
            priority=priority,
            title=title,
            description=description,
            due_at=payload.due_at,
            created_by_user=created_by_user,
            assigned_to_user=assigned_to_user,
        )
        if self._notification_service is not None:
            await self._notification_service.notify_for_upcoming_maintenance(task)
        return task

    async def list_tasks(self, *, equipment_id=None, status: str | None = None, priority: str | None = None, assigned_to_user_id=None):
        if status is not None and status not in VALID_MAINTENANCE_TASK_STATUSES:
            raise ValueError("Unsupported maintenance task status filter.")
        if priority is not None and priority not in VALID_MAINTENANCE_TASK_PRIORITIES:
            raise ValueError("Unsupported maintenance task priority filter.")

        return await self._maintenance_task_repository.list_all(
            equipment_id=equipment_id,
            status=status,
            priority=priority,
            assigned_to_user_id=assigned_to_user_id,
        )

    async def get_task(self, task_id):
        return await self._maintenance_task_repository.get_by_id(task_id)

    async def update_task(self, task_id, payload: MaintenanceTaskUpdate):
        task = await self._maintenance_task_repository.get_by_id(task_id)
        if task is None:
            return None

        update_data = payload.model_dump(exclude_unset=True)

        if task.status == MAINTENANCE_TASK_STATUS_DONE and "status" in update_data:
            raise ValueError("Completed maintenance task cannot change status.")

        if task.status == MAINTENANCE_TASK_STATUS_CANCELLED and "status" in update_data:
            raise ValueError("Cancelled maintenance task cannot change status.")

        assigned_to_user = UNSET
        if "assigned_to_user_id" in update_data:
            if update_data["assigned_to_user_id"] is None:
                assigned_to_user = None
            else:
                assigned_to_user = await self._user_repository.get_by_id(update_data["assigned_to_user_id"])
                if assigned_to_user is None:
                    raise ValueError("Assigned user was not found.")

        status = UNSET
        if "status" in update_data:
            status = self._validate_status_transition(task.status, update_data["status"])

        priority = UNSET
        if "priority" in update_data:
            priority = self._validate_priority(update_data["priority"])

        updated_task = await self._maintenance_task_repository.update(
            task,
            status=status,
            priority=priority,
            title=update_data["title"] if "title" in update_data else UNSET,
            description=update_data["description"] if "description" in update_data else UNSET,
            due_at=update_data["due_at"] if "due_at" in update_data else UNSET,
            assigned_to_user=assigned_to_user,
        )
        if self._notification_service is not None:
            await self._notification_service.notify_for_upcoming_maintenance(updated_task)
        return updated_task

    async def complete_task(self, task_id, payload: MaintenanceTaskComplete, *, actor_user_id):
        task = await self._maintenance_task_repository.get_by_id(task_id)
        if task is None:
            return None

        if task.status == MAINTENANCE_TASK_STATUS_DONE:
            raise ValueError("Maintenance task is already completed.")
        if task.status == MAINTENANCE_TASK_STATUS_CANCELLED:
            raise ValueError("Cancelled maintenance task cannot be completed.")

        existing_record = await self._maintenance_record_repository.get_by_task_id(task.id)
        if existing_record is not None:
            raise ValueError("Maintenance record already exists for this task.")

        performed_by_user_id = payload.performed_by_user_id or actor_user_id
        performed_by_user = await self._user_repository.get_by_id(performed_by_user_id)
        if performed_by_user is None:
            raise ValueError("Performing user was not found.")

        record = await self._maintenance_record_repository.create(
            task=task,
            equipment=task.equipment,
            performed_by_user=performed_by_user,
            summary=payload.summary,
            details=payload.details,
            performed_at=payload.performed_at,
        )
        await self._maintenance_task_repository.update(
            task,
            status=MAINTENANCE_TASK_STATUS_DONE,
            completed_at=payload.performed_at,
        )
        return await self._maintenance_record_repository.get_by_id(record.id)

    @staticmethod
    def _validate_plan_compatibility(plan, equipment) -> None:
        if plan.equipment_id is not None and plan.equipment_id != equipment.id:
            raise ValueError("Maintenance plan is bound to another equipment unit.")
        if plan.equipment_type_id is not None and plan.equipment_type_id != equipment.equipment_type_id:
            raise ValueError("Maintenance plan equipment type does not match the target equipment.")

    @staticmethod
    def _validate_priority(priority: str) -> str:
        if priority not in VALID_MAINTENANCE_TASK_PRIORITIES:
            raise ValueError("Unsupported maintenance task priority.")
        return priority

    @staticmethod
    def _validate_status_transition(current_status: str, new_status: str) -> str:
        if new_status not in VALID_MAINTENANCE_TASK_STATUSES:
            raise ValueError("Unsupported maintenance task status.")
        if new_status == MAINTENANCE_TASK_STATUS_DONE:
            raise ValueError("Maintenance task completion must go through the completion endpoint.")
        if current_status == MAINTENANCE_TASK_STATUS_OPEN and new_status in {
            MAINTENANCE_TASK_STATUS_OPEN,
            MAINTENANCE_TASK_STATUS_IN_PROGRESS,
            MAINTENANCE_TASK_STATUS_CANCELLED,
        }:
            return new_status
        if current_status == MAINTENANCE_TASK_STATUS_IN_PROGRESS and new_status in {
            MAINTENANCE_TASK_STATUS_IN_PROGRESS,
            MAINTENANCE_TASK_STATUS_CANCELLED,
        }:
            return new_status
        raise ValueError("Unsupported maintenance task status transition.")
