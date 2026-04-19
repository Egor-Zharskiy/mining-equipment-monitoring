from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.dependencies.auth import require_permissions
from app.repositories.equipment_parameter_state_repository import EquipmentParameterStateRepository
from app.repositories.equipment_state_repository import EquipmentStateRepository
from app.repositories.event_repository import EventRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.telemetry_evaluation_repository import TelemetryEvaluationRepository
from app.repositories.threshold_rule_repository import ThresholdRuleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.equipment_state import EquipmentParameterStateRead, EquipmentStateDetailRead, EquipmentStateRead
from app.services.equipment_state_service import EquipmentStateService
from app.services.event_service import EventService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/equipment-states", tags=["Equipment States"])


def get_equipment_state_service(session: AsyncSession) -> EquipmentStateService:
    """Build the equipment state service with its repository dependencies."""

    return EquipmentStateService(
        ThresholdRuleRepository(session),
        TelemetryEvaluationRepository(session),
        EquipmentParameterStateRepository(session),
        EquipmentStateRepository(session),
        EventService(
            EventRepository(session),
            NotificationService(NotificationRepository(session), UserRepository(session)),
        ),
    )


@router.get("/", response_model=list[EquipmentStateRead], status_code=status.HTTP_200_OK)
async def list_equipment_states(
    status_filter: str | None = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.read")),
) -> list[EquipmentStateRead]:
    """Return current equipment state snapshots optionally filtered by status."""

    service = get_equipment_state_service(session)

    try:
        equipment_states = await service.list_equipment_states(status=status_filter)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return [EquipmentStateRead.model_validate(item) for item in equipment_states]


@router.get("/{equipment_id}", response_model=EquipmentStateDetailRead, status_code=status.HTTP_200_OK)
async def get_equipment_state(
    equipment_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.read")),
) -> EquipmentStateDetailRead:
    """Return the current detailed monitoring state of an equipment unit."""

    service = get_equipment_state_service(session)
    state, parameter_states = await service.get_equipment_state(equipment_id)

    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment state not found.")

    payload = EquipmentStateRead.model_validate(state).model_dump()
    payload["parameter_states"] = [
        EquipmentParameterStateRead.model_validate(item).model_dump() for item in parameter_states
    ]
    return EquipmentStateDetailRead.model_validate(payload)
