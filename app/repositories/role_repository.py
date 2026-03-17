from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Permission, Role


class RoleRepository:
    """Handles database access for role entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the active asynchronous database session."""

        self._session = session

    async def create(
            self,
            *,
            name: str,
            description: str | None,
            permissions: list[Permission],
    ) -> Role:
        """Persist a new role with its permission assignments."""

        role = Role(name=name, description=description,
                    permissions=permissions)
        self._session.add(role)
        await self._session.flush()
        await self._session.refresh(role)
        return await self.get_by_id(role.id)  # type: ignore[return-value]

    async def get_by_id(self, role_id: UUID) -> Role | None:
        """Return a role by identifier with eager-loaded permissions."""

        result = await self._session.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Role | None:
        """Return a role by its unique name with eager-loaded permissions."""

        result = await self._session.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.name == name)
        )
        return result.scalar_one_or_none()

    async def get_many_by_ids(self, role_ids: list[UUID]) -> list[Role]:
        """Return roles matching the provided identifiers."""

        if not role_ids:
            return []

        result = await self._session.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id.in_(role_ids))
        )
        return list(result.scalars().unique().all())

    async def list_all(self) -> list[Role]:
        """Return all roles ordered by name with eager-loaded permissions."""

        result = await self._session.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .order_by(Role.name)
        )
        return list(result.scalars().unique().all())
