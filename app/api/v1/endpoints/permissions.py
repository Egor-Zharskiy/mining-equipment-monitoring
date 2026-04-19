from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.audit import get_audit_service
from app.db.session import get_async_session
from app.dependencies.auth import require_permissions
from app.repositories.permission_repository import PermissionRepository
from app.schemas.permission import PermissionCreate, PermissionRead
from app.services.audit_service import AuditService
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.post("/", response_model=PermissionRead, status_code=status.HTTP_201_CREATED)
async def create_permission(
    payload: PermissionCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("roles.manage")),
) -> PermissionRead:
    """Create a new permission."""

    service = PermissionService(PermissionRepository(session))

    try:
        permission = await service.create_permission(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    await get_audit_service(session).log_action(
        actor_user_id=current_user.id,
        action="create",
        resource_type="permissions",
        resource_id=permission.id,
        status_code=status.HTTP_201_CREATED,
        details=AuditService.build_details(
            request_data=payload.model_dump(mode="json", exclude_none=True),
        ),
    )
    return PermissionRead.model_validate(permission)


@router.get("/", response_model=list[PermissionRead], status_code=status.HTTP_200_OK)
async def list_permissions(
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("permissions.read")),
) -> list[PermissionRead]:
    """Return all permissions."""

    service = PermissionService(PermissionRepository(session))
    permissions = await service.list_permissions()
    return [PermissionRead.model_validate(permission) for permission in permissions]
