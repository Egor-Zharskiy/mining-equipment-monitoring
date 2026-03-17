from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.schemas.role import RoleCreate


class RoleService:
    """Encapsulates role-related business rules."""

    def __init__(
            self,
            role_repository: RoleRepository,
            permission_repository: PermissionRepository,
    ) -> None:
        """Store repository dependencies used by the service."""

        self._role_repository = role_repository
        self._permission_repository = permission_repository

    async def create_role(self, payload: RoleCreate):
        """Create a role and attach the requested permissions."""

        existing_role = await self._role_repository.get_by_name(payload.name)
        if existing_role is not None:
            raise ValueError(
                f"Role with name '{payload.name}' already exists.")

        permissions = await self._permission_repository.get_many_by_ids(
            payload.permission_ids)
        if len(permissions) != len(set(payload.permission_ids)):
            raise ValueError("One or more permissions were not found.")

        return await self._role_repository.create(
            name=payload.name,
            description=payload.description,
            permissions=permissions,
        )

    async def list_roles(self):
        """Return all roles."""

        return await self._role_repository.list_all()
