from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.dependencies.auth import require_permissions
from app.repositories.maintenance_record_repository import MaintenanceRecordRepository
from app.schemas.maintenance import MaintenanceRecordRead
from app.services.maintenance_record_service import MaintenanceRecordService

router = APIRouter(prefix="/maintenance-records", tags=["Maintenance Records"])


def get_maintenance_record_service(session: AsyncSession) -> MaintenanceRecordService:
    return MaintenanceRecordService(MaintenanceRecordRepository(session))


@router.get("/", response_model=list[MaintenanceRecordRead], status_code=status.HTTP_200_OK)
async def list_maintenance_records(
    equipment_id: UUID | None = Query(default=None),
    task_id: UUID | None = Query(default=None),
    performed_by_user_id: UUID | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("maintenance.read")),
) -> list[MaintenanceRecordRead]:
    service = get_maintenance_record_service(session)
    try:
        records = await service.list_records(
            equipment_id=equipment_id,
            task_id=task_id,
            performed_by_user_id=performed_by_user_id,
            date_from=date_from,
            date_to=date_to,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return [MaintenanceRecordRead.model_validate(record) for record in records]


@router.get("/{record_id}", response_model=MaintenanceRecordRead, status_code=status.HTTP_200_OK)
async def get_maintenance_record(
    record_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("maintenance.read")),
) -> MaintenanceRecordRead:
    service = get_maintenance_record_service(session)
    record = await service.get_record(record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found.")
    return MaintenanceRecordRead.model_validate(record)
