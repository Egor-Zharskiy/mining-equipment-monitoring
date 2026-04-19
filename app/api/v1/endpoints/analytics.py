from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.dependencies.auth import require_permissions
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.equipment_repository import EquipmentRepository
from app.repositories.equipment_type_repository import EquipmentTypeRepository
from app.repositories.parameter_repository import ParameterRepository
from app.repositories.user_repository import UserRepository
from app.schemas.analytics import (
    AnalyticsOverviewRead,
    EquipmentStatusAnalyticsRead,
    EventAnalyticsRead,
    MaintenanceAnalyticsRead,
    NotificationAnalyticsRead,
    TelemetryHistoryAnalyticsRead,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_analytics_service(session: AsyncSession) -> AnalyticsService:
    return AnalyticsService(
        AnalyticsRepository(session),
        EquipmentRepository(session),
        EquipmentTypeRepository(session),
        ParameterRepository(session),
        UserRepository(session),
    )


@router.get("/overview", response_model=AnalyticsOverviewRead, status_code=status.HTTP_200_OK)
async def get_analytics_overview(
    days: int = Query(default=7, ge=1, le=365),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("analytics.read")),
) -> AnalyticsOverviewRead:
    service = get_analytics_service(session)
    return await service.get_overview(days=days)


@router.get("/equipment-status", response_model=EquipmentStatusAnalyticsRead, status_code=status.HTTP_200_OK)
async def get_equipment_status_analytics(
    equipment_type_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("analytics.read")),
) -> EquipmentStatusAnalyticsRead:
    service = get_analytics_service(session)
    try:
        return await service.get_equipment_status_analytics(equipment_type_id=equipment_type_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/events", response_model=EventAnalyticsRead, status_code=status.HTTP_200_OK)
async def get_event_analytics(
    equipment_id: UUID | None = Query(default=None),
    severity: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("analytics.read")),
) -> EventAnalyticsRead:
    service = get_analytics_service(session)
    try:
        return await service.get_event_analytics(
            equipment_id=equipment_id,
            severity=severity,
            event_type=event_type,
            date_from=date_from,
            date_to=date_to,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/telemetry-history", response_model=TelemetryHistoryAnalyticsRead, status_code=status.HTTP_200_OK)
async def get_telemetry_history_analytics(
    equipment_id: UUID = Query(),
    parameter_id: UUID = Query(),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("analytics.read")),
) -> TelemetryHistoryAnalyticsRead:
    service = get_analytics_service(session)
    try:
        return await service.get_telemetry_history_analytics(
            equipment_id=equipment_id,
            parameter_id=parameter_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/maintenance", response_model=MaintenanceAnalyticsRead, status_code=status.HTTP_200_OK)
async def get_maintenance_analytics(
    equipment_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("analytics.read")),
) -> MaintenanceAnalyticsRead:
    service = get_analytics_service(session)
    try:
        return await service.get_maintenance_analytics(equipment_id=equipment_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/notifications", response_model=NotificationAnalyticsRead, status_code=status.HTTP_200_OK)
async def get_notification_analytics(
    recipient_user_id: UUID | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("analytics.read")),
) -> NotificationAnalyticsRead:
    service = get_analytics_service(session)
    try:
        return await service.get_notification_analytics(
            recipient_user_id=recipient_user_id,
            date_from=date_from,
            date_to=date_to,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
