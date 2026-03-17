from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Permission


class PermissionRepository:
    """Handles database access for permission entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the active asynchronous database session."""

        self._session = session

    async def create(self, *, code: str,
                     description: str | None) -> Permission:
        """Persist a new permission in the database."""

        permission = Permission(code=code, description=description)
        self._session.add(permission)
        await self._session.flush()
        await self._session.refresh(permission)
        return permission

    async def get_by_code(self, code: str) -> Permission | None:
        """Return a permission by its unique code."""

        result = await self._session.execute(
            select(Permission).where(Permission.code == code))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Permission]:
        """Return all permissions ordered by code."""

        result = await self._session.execute(
            select(Permission).order_by(Permission.code))
        return list(result.scalars().all())

    async def get_many_by_ids(self, permission_ids: list[UUID]) -> list[
        Permission]:
        """Return permissions matching the provided identifiers."""

        if not permission_ids:
            return []

        result = await self._session.execute(
            select(Permission).where(Permission.id.in_(permission_ids)))
        return list(result.scalars().all())
