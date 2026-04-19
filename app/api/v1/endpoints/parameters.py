from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.audit import get_audit_service
from app.db.session import get_async_session
from app.dependencies.auth import require_permissions
from app.repositories.parameter_repository import ParameterRepository
from app.schemas.parameter import ParameterCreate, ParameterRead, ParameterUpdate
from app.services.audit_service import AuditService
from app.services.parameter_service import ParameterService

router = APIRouter(prefix="/parameters", tags=["Parameters"])


@router.post("/", response_model=ParameterRead, status_code=status.HTTP_201_CREATED)
async def create_parameter(
    payload: ParameterCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.manage")),
) -> ParameterRead:
    """Create a new monitoring parameter."""

    service = ParameterService(ParameterRepository(session))

    try:
        parameter = await service.create_parameter(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="create",
        resource_type="parameters",
        resource_id=parameter.id,
        status_code=status.HTTP_201_CREATED,
        details=AuditService.build_details(
            request_data=payload.model_dump(mode="json", exclude_none=True),
        ),
    )
    return ParameterRead.model_validate(parameter)


@router.get("/", response_model=list[ParameterRead], status_code=status.HTTP_200_OK)
async def list_parameters(
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.read")),
) -> list[ParameterRead]:
    """Return all monitoring parameters."""

    service = ParameterService(ParameterRepository(session))
    parameters = await service.list_parameters()
    return [ParameterRead.model_validate(parameter) for parameter in parameters]


@router.get("/{parameter_id}", response_model=ParameterRead, status_code=status.HTTP_200_OK)
async def get_parameter(
    parameter_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.read")),
) -> ParameterRead:
    """Return a single parameter by identifier."""

    service = ParameterService(ParameterRepository(session))
    parameter = await service.get_parameter(parameter_id)

    if parameter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parameter not found.")

    return ParameterRead.model_validate(parameter)


@router.patch("/{parameter_id}", response_model=ParameterRead, status_code=status.HTTP_200_OK)
async def update_parameter(
    parameter_id: UUID,
    payload: ParameterUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.manage")),
) -> ParameterRead:
    """Update an existing monitoring parameter."""

    service = ParameterService(ParameterRepository(session))

    try:
        parameter = await service.update_parameter(parameter_id, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    if parameter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parameter not found.")

    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="update",
        resource_type="parameters",
        resource_id=parameter.id,
        status_code=status.HTTP_200_OK,
        details=AuditService.build_details(
            request_data=payload.model_dump(mode="json", exclude_none=True),
        ),
    )

    return ParameterRead.model_validate(parameter)


@router.delete("/{parameter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parameter(
    parameter_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("equipment.manage")),
) -> None:
    """Delete an existing monitoring parameter."""

    service = ParameterService(ParameterRepository(session))

    try:
        parameter = await service.delete_parameter(parameter_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    if parameter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parameter not found.")

    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="delete",
        resource_type="parameters",
        resource_id=parameter.id,
        status_code=status.HTTP_204_NO_CONTENT,
    )
