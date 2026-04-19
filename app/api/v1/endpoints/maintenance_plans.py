from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.audit import get_audit_service
from app.db.session import get_async_session
from app.dependencies.auth import require_permissions
from app.repositories.equipment_repository import EquipmentRepository
from app.repositories.equipment_type_repository import EquipmentTypeRepository
from app.repositories.maintenance_plan_repository import MaintenancePlanRepository
from app.schemas.maintenance import MaintenancePlanCreate, MaintenancePlanRead, MaintenancePlanUpdate
from app.services.audit_service import AuditService
from app.services.maintenance_plan_service import MaintenancePlanService

router = APIRouter(prefix="/maintenance-plans", tags=["Maintenance Plans"])


def get_maintenance_plan_service(session: AsyncSession) -> MaintenancePlanService:
    return MaintenancePlanService(
        MaintenancePlanRepository(session),
        EquipmentRepository(session),
        EquipmentTypeRepository(session),
    )


@router.post("/", response_model=MaintenancePlanRead, status_code=status.HTTP_201_CREATED)
async def create_maintenance_plan(
    payload: MaintenancePlanCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("maintenance.manage")),
) -> MaintenancePlanRead:
    service = get_maintenance_plan_service(session)
    try:
        plan = await service.create_plan(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="create",
        resource_type="maintenance_plans",
        resource_id=plan.id,
        status_code=status.HTTP_201_CREATED,
        details=AuditService.build_details(
            request_data=payload.model_dump(mode="json", exclude_none=True),
        ),
    )
    return MaintenancePlanRead.model_validate(plan)


@router.get("/", response_model=list[MaintenancePlanRead], status_code=status.HTTP_200_OK)
async def list_maintenance_plans(
    equipment_type_id: UUID | None = Query(default=None),
    equipment_id: UUID | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("maintenance.read")),
) -> list[MaintenancePlanRead]:
    service = get_maintenance_plan_service(session)
    plans = await service.list_plans(
        equipment_type_id=equipment_type_id,
        equipment_id=equipment_id,
        is_active=is_active,
    )
    return [MaintenancePlanRead.model_validate(plan) for plan in plans]


@router.get("/{plan_id}", response_model=MaintenancePlanRead, status_code=status.HTTP_200_OK)
async def get_maintenance_plan(
    plan_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("maintenance.read")),
) -> MaintenancePlanRead:
    service = get_maintenance_plan_service(session)
    plan = await service.get_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance plan not found.")
    return MaintenancePlanRead.model_validate(plan)


@router.patch("/{plan_id}", response_model=MaintenancePlanRead, status_code=status.HTTP_200_OK)
async def update_maintenance_plan(
    plan_id: UUID,
    payload: MaintenancePlanUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("maintenance.manage")),
) -> MaintenancePlanRead:
    service = get_maintenance_plan_service(session)
    try:
        plan = await service.update_plan(plan_id, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance plan not found.")
    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="update",
        resource_type="maintenance_plans",
        resource_id=plan.id,
        status_code=status.HTTP_200_OK,
        details=AuditService.build_details(
            request_data=payload.model_dump(mode="json", exclude_none=True),
        ),
    )
    return MaintenancePlanRead.model_validate(plan)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_maintenance_plan(
    plan_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("maintenance.manage")),
) -> None:
    service = get_maintenance_plan_service(session)
    plan = await service.delete_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance plan not found.")
    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="delete",
        resource_type="maintenance_plans",
        resource_id=plan.id,
        status_code=status.HTTP_204_NO_CONTENT,
    )
