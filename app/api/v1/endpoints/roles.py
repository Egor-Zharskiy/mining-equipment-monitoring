from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.audit import get_audit_service
from app.db.session import get_async_session
from app.dependencies.auth import require_permissions
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.schemas.role import RoleCreate, RoleRead
from app.services.audit_service import AuditService
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("roles.manage")),
) -> RoleRead:
    """Create a new role with optional permissions."""

    service = RoleService(RoleRepository(session), PermissionRepository(session))

    try:
        role = await service.create_role(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="create",
        resource_type="roles",
        resource_id=role.id,
        status_code=status.HTTP_201_CREATED,
        details=AuditService.build_details(
            request_data=payload.model_dump(mode="json", exclude_none=True),
        ),
    )
    return RoleRead.model_validate(role)


@router.get("/", response_model=list[RoleRead], status_code=status.HTTP_200_OK)
async def list_roles(
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("roles.read")),
) -> list[RoleRead]:
    """Return all roles."""

    service = RoleService(RoleRepository(session), PermissionRepository(session))
    roles = await service.list_roles()
    return [RoleRead.model_validate(role) for role in roles]
