from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.schemas.role import RoleCreate, RoleRead
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    session: AsyncSession = Depends(get_async_session),
) -> RoleRead:
    """Create a new role with optional permissions."""

    service = RoleService(RoleRepository(session), PermissionRepository(session))

    try:
        role = await service.create_role(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return RoleRead.model_validate(role)


@router.get("/", response_model=list[RoleRead], status_code=status.HTTP_200_OK)
async def list_roles(
    session: AsyncSession = Depends(get_async_session),
) -> list[RoleRead]:
    """Return all roles."""

    service = RoleService(RoleRepository(session), PermissionRepository(session))
    roles = await service.list_roles()
    return [RoleRead.model_validate(role) for role in roles]
