from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.dependencies.auth import require_permissions
from app.repositories.equipment_type_parameter_repository import EquipmentTypeParameterRepository
from app.repositories.equipment_type_repository import EquipmentTypeRepository
from app.repositories.parameter_repository import ParameterRepository
from app.repositories.threshold_rule_repository import ThresholdRuleRepository
from app.schemas.threshold_rule import ThresholdRuleCreate, ThresholdRuleRead, ThresholdRuleUpdate
from app.services.threshold_rule_service import ThresholdRuleService

router = APIRouter(prefix="/threshold-rules", tags=["Threshold Rules"])


def get_threshold_rule_service(session: AsyncSession) -> ThresholdRuleService:
    """Build the threshold rule service with its repository dependencies."""

    return ThresholdRuleService(
        ThresholdRuleRepository(session),
        EquipmentTypeRepository(session),
        ParameterRepository(session),
        EquipmentTypeParameterRepository(session),
    )


@router.post("/", response_model=ThresholdRuleRead, status_code=status.HTTP_201_CREATED)
async def create_threshold_rule(
    payload: ThresholdRuleCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("threshold_rules.manage")),
) -> ThresholdRuleRead:
    """Create a new threshold rule."""

    service = get_threshold_rule_service(session)

    try:
        rule = await service.create_threshold_rule(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return ThresholdRuleRead.model_validate(rule)


@router.get("/", response_model=list[ThresholdRuleRead], status_code=status.HTTP_200_OK)
async def list_threshold_rules(
    equipment_type_id: UUID | None = Query(default=None),
    parameter_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("threshold_rules.read")),
) -> list[ThresholdRuleRead]:
    """Return threshold rules optionally filtered by equipment type or parameter."""

    service = get_threshold_rule_service(session)
    rules = await service.list_threshold_rules(equipment_type_id=equipment_type_id, parameter_id=parameter_id)
    return [ThresholdRuleRead.model_validate(rule) for rule in rules]


@router.get("/{rule_id}", response_model=ThresholdRuleRead, status_code=status.HTTP_200_OK)
async def get_threshold_rule(
    rule_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("threshold_rules.read")),
) -> ThresholdRuleRead:
    """Return a threshold rule by identifier."""

    service = get_threshold_rule_service(session)
    rule = await service.get_threshold_rule(rule_id)

    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threshold rule not found.")

    return ThresholdRuleRead.model_validate(rule)


@router.patch("/{rule_id}", response_model=ThresholdRuleRead, status_code=status.HTTP_200_OK)
async def update_threshold_rule(
    rule_id: UUID,
    payload: ThresholdRuleUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("threshold_rules.manage")),
) -> ThresholdRuleRead:
    """Update an existing threshold rule."""

    service = get_threshold_rule_service(session)

    try:
        rule = await service.update_threshold_rule(rule_id, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threshold rule not found.")

    return ThresholdRuleRead.model_validate(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_threshold_rule(
    rule_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("threshold_rules.manage")),
) -> None:
    """Delete an existing threshold rule."""

    service = get_threshold_rule_service(session)
    rule = await service.delete_threshold_rule(rule_id)

    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threshold rule not found.")
