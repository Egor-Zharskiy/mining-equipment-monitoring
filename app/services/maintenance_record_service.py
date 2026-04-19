from app.repositories.maintenance_record_repository import MaintenanceRecordRepository


class MaintenanceRecordService:
    """Encapsulates read-only maintenance record queries."""

    def __init__(self, maintenance_record_repository: MaintenanceRecordRepository) -> None:
        self._maintenance_record_repository = maintenance_record_repository

    async def list_records(
        self,
        *,
        equipment_id=None,
        task_id=None,
        performed_by_user_id=None,
        date_from=None,
        date_to=None,
    ):
        if date_from is not None and date_to is not None and date_from > date_to:
            raise ValueError("date_from must be less than or equal to date_to.")

        return await self._maintenance_record_repository.list_all(
            equipment_id=equipment_id,
            task_id=task_id,
            performed_by_user_id=performed_by_user_id,
            date_from=date_from,
            date_to=date_to,
        )

    async def get_record(self, record_id):
        return await self._maintenance_record_repository.get_by_id(record_id)
