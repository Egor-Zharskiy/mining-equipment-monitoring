from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user, require_permissions
from app.db.session import get_async_session
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserRead, UserSelfUpdate, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("users.create")),
) -> UserRead:
    """Create a new user with role assignments."""

    service = UserService(UserRepository(session), RoleRepository(session))

    try:
        user = await service.create_user(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return UserRead.model_validate(user)


@router.get("/", response_model=list[UserRead], status_code=status.HTTP_200_OK)
async def list_users(
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("users.read")),
) -> list[UserRead]:
    """Return all users with roles and permissions."""

    service = UserService(UserRepository(session), RoleRepository(session))
    users = await service.list_users()
    return [UserRead.model_validate(user) for user in users]


@router.get("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
async def get_my_profile(
    current_user=Depends(get_current_user),
) -> UserRead:
    """Return the currently authenticated user."""

    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
async def update_my_profile(
    payload: UserSelfUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
) -> UserRead:
    """Update the currently authenticated user profile."""

    service = UserService(UserRepository(session), RoleRepository(session))

    try:
        user = await service.update_current_user(current_user.id, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return UserRead.model_validate(user)


@router.get("/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("users.read")),
) -> UserRead:
    """Return a single user by identifier."""

    service = UserService(UserRepository(session), RoleRepository(session))
    user = await service.get_user(user_id)

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return UserRead.model_validate(user)


@router.patch("/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("users.update")),
) -> UserRead:
    """Update an existing user."""

    service = UserService(UserRepository(session), RoleRepository(session))

    try:
        user = await service.update_user(user_id, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return UserRead.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("users.delete")),
) -> None:
    """Delete an existing user."""

    service = UserService(UserRepository(session), RoleRepository(session))

    try:
        user = await service.delete_user(user_id, actor_user_id=current_user.id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
