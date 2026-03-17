from collections.abc import Callable
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.repositories.user_repository import UserRepository
from app.services.security_service import SecurityService

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_async_session),
):
    """Resolve the current authenticated user from a bearer token."""

    token = credentials.credentials

    try:
        payload = SecurityService.decode_access_token(token)
        user_id = UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
        ) from error

    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user was not found.",
        )

    return user


def require_permissions(*required_permissions: str) -> Callable:
    """Create a dependency that checks the current user permissions."""

    async def permission_checker(current_user=Depends(get_current_user)):
        user_permissions = {
            permission.code
            for role in current_user.roles
            for permission in role.permissions
        }
        missing_permissions = [
            permission for permission in required_permissions if permission not in user_permissions
        ]
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing_permissions)}.",
            )
        return current_user

    return permission_checker
