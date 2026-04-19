import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.audit import get_audit_service
from app.core.profiling import log_auth_profile, profile_auth_step
from app.db.session import get_async_session
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserRead
from app.services.audit_service import AuditService
from app.services.security_service import SecurityService
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_async_session),
) -> TokenResponse:
    """Authenticate a user and return a bearer access token."""

    total_start = time.perf_counter()
    service = UserService(UserRepository(session), RoleRepository(session))

    try:
        user = await service.authenticate_user(email=str(payload.email), password=payload.password)

    except ValueError as error:
        logger.warning("auth_login_rejected", extra={"reason": str(error)})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    if user is None:
        logger.warning("auth_login_failed", extra={"reason": "invalid_credentials"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    with profile_auth_step("auth.login.audit", email=payload.email, user_id=user.id):
        await get_audit_service(session).log_action(
            actor_user_id=user.id,
            action="login",
            resource_type="auth",
            resource_id=user.id,
            status_code=status.HTTP_200_OK,
            details=AuditService.build_details(
                request_data=payload.model_dump(mode="json", exclude_none=True),
            ),
        )

    with profile_auth_step("auth.login.create_access_token", email=payload.email, user_id=user.id):
        access_token = SecurityService.create_access_token(user_id=user.id)

    with profile_auth_step("auth.login.serialize_user", email=payload.email, user_id=user.id):
        user_payload = UserRead.model_validate(user)

    log_auth_profile(
        "auth.login.total",
        time.perf_counter() - total_start,
        email=payload.email,
        user_id=user.id,
    )
    logger.info("auth_login_success", extra={"user_id": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        user=user_payload,
    )
