import time
from uuid import UUID

from app.core.profiling import log_auth_profile, profile_auth_step
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserSelfUpdate, UserUpdate
from app.services.security_service import SecurityService


class UserService:
    """Encapsulates user-related business rules."""

    def __init__(self, user_repository: UserRepository,
                 role_repository: RoleRepository) -> None:
        """Store repository dependencies used by the service."""

        self._user_repository = user_repository
        self._role_repository = role_repository

    async def create_user(self, payload: UserCreate):
        """Create a new user and assign the requested roles."""

        existing_email = await self._user_repository.get_by_email(
            payload.email)
        if existing_email is not None:
            raise ValueError(
                f"User with email '{payload.email}' already exists.")

        existing_username = await self._user_repository.get_by_username(
            payload.username)
        if existing_username is not None:
            raise ValueError(
                f"User with username '{payload.username}' already exists.")

        roles = await self._role_repository.get_many_by_ids(payload.role_ids)
        if len(roles) != len(set(payload.role_ids)):
            raise ValueError("One or more roles were not found.")

        return await self._user_repository.create(
            username=payload.username,
            email=payload.email,
            hashed_password=SecurityService.hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            is_active=payload.is_active,
            roles=roles,
        )

    async def get_user(self, user_id: UUID):
        """Return a user by identifier."""

        return await self._user_repository.get_by_id(user_id)

    async def list_users(self):
        """Return all users."""

        return await self._user_repository.list_all()

    async def update_user(self, user_id: UUID, payload: UserUpdate):
        """Update an existing user and optionally replace assigned roles."""

        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            return None

        await self._ensure_unique_user_fields(
            current_user_id=user.id,
            email=str(payload.email) if payload.email is not None else None,
            username=payload.username,
        )

        roles = None
        if payload.role_ids is not None:
            roles = await self._role_repository.get_many_by_ids(payload.role_ids)
            if len(roles) != len(set(payload.role_ids)):
                raise ValueError("One or more roles were not found.")

        hashed_password = None
        if payload.password is not None:
            hashed_password = SecurityService.hash_password(payload.password)

        return await self._user_repository.update(
            user,
            username=payload.username,
            email=str(payload.email) if payload.email is not None else None,
            hashed_password=hashed_password,
            first_name=payload.first_name,
            last_name=payload.last_name,
            is_active=payload.is_active,
            roles=roles,
        )

    async def update_current_user(self, user_id: UUID, payload: UserSelfUpdate):
        """Update the current user profile without role changes."""

        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            return None

        await self._ensure_unique_user_fields(
            current_user_id=user.id,
            email=str(payload.email) if payload.email is not None else None,
            username=payload.username,
        )

        return await self._user_repository.update(
            user,
            username=payload.username,
            email=str(payload.email) if payload.email is not None else None,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )

    async def delete_user(self, user_id: UUID, *, actor_user_id: UUID):
        """Delete a user unless the target is the current actor."""

        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            return None

        if user.id == actor_user_id:
            raise ValueError("You cannot delete your own account.")

        await self._user_repository.delete(user)
        return user

    async def authenticate_user(self, *, email: str, password: str):
        """Authenticate a user by email and password."""

        total_start = time.perf_counter()
        user = await self._user_repository.get_auth_by_email(email)
        if user is None:
            log_auth_profile(
                "user_service.authenticate_user.total",
                time.perf_counter() - total_start,
                email=email,
                result="not_found",
            )
            return None

        with profile_auth_step("user_service.authenticate_user.verify_password", email=email):
            is_valid_password = SecurityService.verify_password(password, user.hashed_password)

        if not is_valid_password:
            log_auth_profile(
                "user_service.authenticate_user.total",
                time.perf_counter() - total_start,
                email=email,
                result="invalid_password",
            )
            return None

        if not user.is_active:
            raise ValueError("User account is inactive.")

        hydrated_user = await self._user_repository.get_by_id(user.id)
        log_auth_profile(
            "user_service.authenticate_user.total",
            time.perf_counter() - total_start,
            email=email,
            user_id=user.id,
            result="success",
        )
        return hydrated_user

    async def _ensure_unique_user_fields(
        self,
        *,
        current_user_id: UUID,
        email: str | None,
        username: str | None,
    ) -> None:
        """Validate email and username uniqueness for updates."""

        if email is not None:
            existing_email = await self._user_repository.get_by_email(email)
            if existing_email is not None and existing_email.id != current_user_id:
                raise ValueError(f"User with email '{email}' already exists.")

        if username is not None:
            existing_username = await self._user_repository.get_by_username(username)
            if existing_username is not None and existing_username.id != current_user_id:
                raise ValueError(f"User with username '{username}' already exists.")
