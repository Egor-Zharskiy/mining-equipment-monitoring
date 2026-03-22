from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.dependencies.auth import require_permissions
from app.repositories.equipment_repository import EquipmentRepository
from app.repositories.equipment_type_repository import EquipmentTypeRepository
from app.schemas.equipment import EquipmentCreate, EquipmentRead, EquipmentUpdate
from app.services.equipment_service import EquipmentService

router = APIRouter(prefix="/equipment", tags=["Equipment"])


@router.post("/", response_model=EquipmentRead, status_code=status.HTTP_201_CREATED)
async def create_equipment(
    payload: EquipmentCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.manage")),
) -> EquipmentRead:
    """Create a new equipment unit."""

    service = EquipmentService(EquipmentRepository(session), EquipmentTypeRepository(session))

    try:
        equipment = await service.create_equipment(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return EquipmentRead.model_validate(equipment)


@router.get("/", response_model=list[EquipmentRead], status_code=status.HTTP_200_OK)
async def list_equipment(
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.read")),
) -> list[EquipmentRead]:
    """Return all equipment units."""

    service = EquipmentService(EquipmentRepository(session), EquipmentTypeRepository(session))
    equipment_units = await service.list_equipment()
    return [EquipmentRead.model_validate(equipment) for equipment in equipment_units]


@router.get("/{equipment_id}", response_model=EquipmentRead, status_code=status.HTTP_200_OK)
async def get_equipment(
    equipment_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.read")),
) -> EquipmentRead:
    """Return a single equipment unit by identifier."""

    service = EquipmentService(EquipmentRepository(session), EquipmentTypeRepository(session))
    equipment = await service.get_equipment(equipment_id)

    if equipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found.")

    return EquipmentRead.model_validate(equipment)


@router.patch("/{equipment_id}", response_model=EquipmentRead, status_code=status.HTTP_200_OK)
async def update_equipment(
    equipment_id: UUID,
    payload: EquipmentUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.manage")),
) -> EquipmentRead:
    """Update an existing equipment unit."""

    service = EquipmentService(EquipmentRepository(session), EquipmentTypeRepository(session))

    try:
        equipment = await service.update_equipment(equipment_id, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    if equipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found.")

    return EquipmentRead.model_validate(equipment)


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment(
    equipment_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.manage")),
) -> None:
    """Delete an existing equipment unit."""

    service = EquipmentService(EquipmentRepository(session), EquipmentTypeRepository(session))
    equipment = await service.delete_equipment(equipment_id)

    if equipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found.")
