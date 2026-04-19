import time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.profiling import is_auth_profiling_enabled, log_auth_profile
from app.models import Role, User
from app.models.permission import Permission


class UserRepository:
    """Handles database access for user entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the active asynchronous database session."""

        self._session = session

    async def create(
            self,
            *,
            username: str,
            email: str,
            hashed_password: str,
            first_name: str,
            last_name: str,
            is_active: bool,
            roles: list,
    ) -> User:
        """Persist a new user with assigned roles."""

        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
            roles=roles,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return await self.get_by_id(user.id)

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Return a user by identifier with roles and permissions loaded."""

        result = await self._execute_profiled(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == user_id),
            step="user_repository.get_by_id",
            user_id=user_id,
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Return a user by email with roles and permissions loaded."""

        result = await self._execute_profiled(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.email == email),
            step="user_repository.get_by_email",
            email=email,
        )
        return result.scalar_one_or_none()

    async def get_auth_by_email(self, email: str) -> User | None:
        """Return a user by email for authentication without eager-loading RBAC relations."""

        result = await self._execute_profiled(
            select(User).where(User.email == email),
            step="user_repository.get_auth_by_email",
            email=email,
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Return a user by username with roles and permissions loaded."""

        result = await self._session.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_many_by_ids(self, user_ids: list[UUID]) -> list[User]:
        """Return users matching the provided identifiers."""

        if not user_ids:
            return []

        result = await self._session.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id.in_(user_ids))
        )
        return list(result.scalars().unique().all())

    async def get_active_with_permission(self, permission_code: str) -> list[User]:
        """Return active users that have a specific permission through assigned roles."""

        result = await self._session.execute(
            select(User)
            .join(User.roles)
            .join(Role.permissions)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.is_active.is_(True))
            .where(Permission.code == permission_code)
            .order_by(User.created_at.desc())
        )
        return list(result.scalars().unique().all())

    async def list_all(self) -> list[User]:
        """Return all users ordered by creation time."""

        result = await self._session.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .order_by(User.created_at.desc())
        )
        return list(result.scalars().unique().all())

    async def update(
        self,
        user: User,
        *,
        username: str | None = None,
        email: str | None = None,
        hashed_password: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        is_active: bool | None = None,
        roles: list[Role] | None = None,
    ) -> User:
        """Update an existing user and return it with eager-loaded relations."""

        if username is not None:
            user.username = username
        if email is not None:
            user.email = email
        if hashed_password is not None:
            user.hashed_password = hashed_password
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if is_active is not None:
            user.is_active = is_active
        if roles is not None:
            user.roles = roles

        await self._session.flush()
        await self._session.refresh(user)
        return await self.get_by_id(user.id)

    async def delete(self, user: User) -> None:
        """Delete an existing user."""

        await self._session.delete(user)

    async def _execute_profiled(self, statement, *, step: str, **details):
        """Profile connection checkout and SQL execution for auth-related user queries."""

        if not is_auth_profiling_enabled():
            return await self._session.execute(statement)

        connection_start = time.perf_counter()
        await self._session.connection()
        log_auth_profile(
            f"{step}.connection",
            time.perf_counter() - connection_start,
            **details,
        )

        execute_start = time.perf_counter()
        result = await self._session.execute(statement)
        log_auth_profile(
            f"{step}.execute",
            time.perf_counter() - execute_start,
            **details,
        )
        return result
