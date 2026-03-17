from app.repositories.permission_repository import PermissionRepository
from app.schemas.permission import PermissionCreate


class PermissionService:
    """Encapsulates permission-related business rules."""

    def __init__(self, permission_repository: PermissionRepository) -> None:
        """Store repository dependencies used by the service."""

        self._permission_repository = permission_repository

    async def create_permission(self, payload: PermissionCreate):
        """Create a permission if its code is not already used."""

        existing_permission = await self._permission_repository.get_by_code(
            payload.code)
        if existing_permission is not None:
            raise ValueError(
                f"Permission with code '{payload.code}' already exists.")

        return await self._permission_repository.create(
            code=payload.code,
            description=payload.description,
        )

    async def list_permissions(self):
        """Return all permissions."""

        return await self._permission_repository.list_all()
