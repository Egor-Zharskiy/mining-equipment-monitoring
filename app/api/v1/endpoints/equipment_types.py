from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.audit import get_audit_service
from app.db.session import get_async_session
from app.dependencies.auth import require_permissions
from app.repositories.equipment_type_repository import EquipmentTypeRepository
from app.schemas.equipment_type import EquipmentTypeCreate, EquipmentTypeRead, EquipmentTypeUpdate
from app.services.audit_service import AuditService
from app.services.equipment_type_service import EquipmentTypeService

router = APIRouter(prefix="/equipment-types", tags=["Equipment Types"])


@router.post("/", response_model=EquipmentTypeRead, status_code=status.HTTP_201_CREATED)
async def create_equipment_type(
    payload: EquipmentTypeCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.manage")),
) -> EquipmentTypeRead:
    """Create a new equipment type."""

    service = EquipmentTypeService(EquipmentTypeRepository(session))

    try:
        equipment_type = await service.create_equipment_type(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="create",
        resource_type="equipment_types",
        resource_id=equipment_type.id,
        status_code=status.HTTP_201_CREATED,
        details=AuditService.build_details(
            request_data=payload.model_dump(mode="json", exclude_none=True),
        ),
    )
    return EquipmentTypeRead.model_validate(equipment_type)


@router.get("/", response_model=list[EquipmentTypeRead], status_code=status.HTTP_200_OK)
async def list_equipment_types(
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.read")),
) -> list[EquipmentTypeRead]:
    """Return all equipment types."""

    service = EquipmentTypeService(EquipmentTypeRepository(session))
    equipment_types = await service.list_equipment_types()
    return [EquipmentTypeRead.model_validate(equipment_type) for equipment_type in equipment_types]


@router.get("/{equipment_type_id}", response_model=EquipmentTypeRead, status_code=status.HTTP_200_OK)
async def get_equipment_type(
    equipment_type_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.read")),
) -> EquipmentTypeRead:
    """Return a single equipment type by identifier."""

    service = EquipmentTypeService(EquipmentTypeRepository(session))
    equipment_type = await service.get_equipment_type(equipment_type_id)

    if equipment_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment type not found.")

    return EquipmentTypeRead.model_validate(equipment_type)


@router.patch("/{equipment_type_id}", response_model=EquipmentTypeRead, status_code=status.HTTP_200_OK)
async def update_equipment_type(
    equipment_type_id: UUID,
    payload: EquipmentTypeUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.manage")),
) -> EquipmentTypeRead:
    """Update an existing equipment type."""

    service = EquipmentTypeService(EquipmentTypeRepository(session))

    try:
        equipment_type = await service.update_equipment_type(equipment_type_id, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    if equipment_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment type not found.")

    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="update",
        resource_type="equipment_types",
        resource_id=equipment_type.id,
        status_code=status.HTTP_200_OK,
        details=AuditService.build_details(
            request_data=payload.model_dump(mode="json", exclude_none=True),
        ),
    )

    return EquipmentTypeRead.model_validate(equipment_type)


@router.delete("/{equipment_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment_type(
    equipment_type_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.manage")),
) -> None:
    """Delete an existing equipment type."""

    service = EquipmentTypeService(EquipmentTypeRepository(session))
    try:
        equipment_type = await service.delete_equipment_type(equipment_type_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    if equipment_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment type not found.")

    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="delete",
        resource_type="equipment_types",
        resource_id=equipment_type.id,
        status_code=status.HTTP_204_NO_CONTENT,
    )
