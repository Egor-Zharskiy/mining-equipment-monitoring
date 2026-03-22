from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.dependencies.auth import require_permissions
from app.repositories.equipment_type_parameter_repository import EquipmentTypeParameterRepository
from app.repositories.equipment_type_repository import EquipmentTypeRepository
from app.repositories.parameter_repository import ParameterRepository
from app.schemas.equipment_type_parameter import EquipmentTypeParameterCreate, EquipmentTypeParameterRead
from app.services.equipment_type_parameter_service import EquipmentTypeParameterService

router = APIRouter(prefix="/equipment-type-parameters", tags=["Equipment Type Parameters"])


@router.post("/", response_model=EquipmentTypeParameterRead, status_code=status.HTTP_201_CREATED)
async def create_equipment_type_parameter(
    payload: EquipmentTypeParameterCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.manage")),
) -> EquipmentTypeParameterRead:
    """Bind a monitoring parameter to an equipment type."""

    service = EquipmentTypeParameterService(
        EquipmentTypeParameterRepository(session),
        EquipmentTypeRepository(session),
        ParameterRepository(session),
    )

    try:
        binding = await service.create_binding(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return EquipmentTypeParameterRead.model_validate(binding)


@router.get("/", response_model=list[EquipmentTypeParameterRead], status_code=status.HTTP_200_OK)
async def list_equipment_type_parameters(
    equipment_type_id: UUID | None = Query(default=None),
    parameter_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.read")),
) -> list[EquipmentTypeParameterRead]:
    """Return parameter bindings, optionally filtered by equipment type or parameter."""

    service = EquipmentTypeParameterService(
        EquipmentTypeParameterRepository(session),
        EquipmentTypeRepository(session),
        ParameterRepository(session),
    )
    bindings = await service.list_bindings(equipment_type_id=equipment_type_id, parameter_id=parameter_id)
    return [EquipmentTypeParameterRead.model_validate(binding) for binding in bindings]


@router.get("/{binding_id}", response_model=EquipmentTypeParameterRead, status_code=status.HTTP_200_OK)
async def get_equipment_type_parameter(
    binding_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.read")),
) -> EquipmentTypeParameterRead:
    """Return a single equipment type parameter binding by identifier."""

    service = EquipmentTypeParameterService(
        EquipmentTypeParameterRepository(session),
        EquipmentTypeRepository(session),
        ParameterRepository(session),
    )
    binding = await service.get_binding(binding_id)

    if binding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment type parameter binding not found.",
        )

    return EquipmentTypeParameterRead.model_validate(binding)


@router.delete("/{binding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment_type_parameter(
    binding_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.manage")),
) -> None:
    """Delete an equipment type parameter binding."""

    service = EquipmentTypeParameterService(
        EquipmentTypeParameterRepository(session),
        EquipmentTypeRepository(session),
        ParameterRepository(session),
    )
    binding = await service.delete_binding(binding_id)

    if binding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment type parameter binding not found.",
        )
