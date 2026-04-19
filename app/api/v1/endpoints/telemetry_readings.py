from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.audit import get_audit_service
from app.db.session import get_async_session
from app.dependencies.auth import require_permissions
from app.repositories.equipment_parameter_state_repository import EquipmentParameterStateRepository
from app.repositories.equipment_state_repository import EquipmentStateRepository
from app.repositories.equipment_repository import EquipmentRepository
from app.repositories.equipment_type_parameter_repository import EquipmentTypeParameterRepository
from app.repositories.event_repository import EventRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.parameter_repository import ParameterRepository
from app.repositories.telemetry_evaluation_repository import TelemetryEvaluationRepository
from app.repositories.telemetry_reading_repository import TelemetryReadingRepository
from app.repositories.threshold_rule_repository import ThresholdRuleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.telemetry_reading import TelemetryReadingCreate, TelemetryReadingRead
from app.services.audit_service import AuditService
from app.services.equipment_state_service import EquipmentStateService
from app.services.event_service import EventService
from app.services.notification_service import NotificationService
from app.services.telemetry_reading_service import TelemetryReadingService

router = APIRouter(prefix="/telemetry-readings", tags=["Telemetry Readings"])


def get_telemetry_reading_service(
    session: AsyncSession,
    background_tasks: BackgroundTasks | None = None,
) -> TelemetryReadingService:
    """Build the telemetry reading service with its repository dependencies."""

    equipment_state_service = EquipmentStateService(
        ThresholdRuleRepository(session),
        TelemetryEvaluationRepository(session),
        EquipmentParameterStateRepository(session),
        EquipmentStateRepository(session),
        EventService(
            EventRepository(session),
            NotificationService(
                NotificationRepository(session),
                UserRepository(session),
                background_tasks=background_tasks,
            ),
        ),
    )

    return TelemetryReadingService(
        TelemetryReadingRepository(session),
        EquipmentRepository(session),
        ParameterRepository(session),
        EquipmentTypeParameterRepository(session),
        equipment_state_service,
    )


@router.post("/", response_model=TelemetryReadingRead, status_code=status.HTTP_201_CREATED)
async def create_telemetry_reading(
    payload: TelemetryReadingCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("telemetry.create")),
) -> TelemetryReadingRead:
    """Create a new raw telemetry reading."""

    service = get_telemetry_reading_service(session, background_tasks)

    try:
        reading = await service.create_reading(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="create",
        resource_type="telemetry_readings",
        resource_id=reading.id,
        status_code=status.HTTP_201_CREATED,
        details=AuditService.build_details(
            request_data=payload.model_dump(mode="json", exclude_none=True),
        ),
    )
    return TelemetryReadingRead.model_validate(reading)


@router.get("/", response_model=list[TelemetryReadingRead], status_code=status.HTTP_200_OK)
async def list_telemetry_readings(
    equipment_id: UUID | None = Query(default=None),
    parameter_id: UUID | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("telemetry.read")),
) -> list[TelemetryReadingRead]:
    """Return telemetry readings optionally filtered by equipment, parameter, or period."""

    service = get_telemetry_reading_service(session)

    try:
        readings = await service.list_readings(
            equipment_id=equipment_id,
            parameter_id=parameter_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return [TelemetryReadingRead.model_validate(reading) for reading in readings]


@router.get("/{reading_id}", response_model=TelemetryReadingRead, status_code=status.HTTP_200_OK)
async def get_telemetry_reading(
    reading_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("telemetry.read")),
) -> TelemetryReadingRead:
    """Return a telemetry reading by identifier."""

    service = get_telemetry_reading_service(session)
    reading = await service.get_reading(reading_id)

    if reading is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemetry reading not found.")

    return TelemetryReadingRead.model_validate(reading)
