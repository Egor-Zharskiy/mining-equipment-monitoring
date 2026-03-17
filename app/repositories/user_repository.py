from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Role, User


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

        result = await self._session.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Return a user by email with roles and permissions loaded."""

        result = await self._session.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.email == email)
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
