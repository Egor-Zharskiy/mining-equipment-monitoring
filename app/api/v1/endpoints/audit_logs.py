from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.dependencies.auth import require_permissions
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit import AuditLogRead
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


def get_audit_service(session: AsyncSession) -> AuditService:
    return AuditService(AuditLogRepository(session))


@router.get("/", response_model=list[AuditLogRead], status_code=status.HTTP_200_OK)
async def list_audit_logs(
    actor_user_id: UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    resource_id: UUID | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("audit.read")),
) -> list[AuditLogRead]:
    service = get_audit_service(session)
    try:
        audit_logs = await service.list_audit_logs(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return [AuditLogRead.model_validate(audit_log) for audit_log in audit_logs]


@router.get("/{audit_log_id}", response_model=AuditLogRead, status_code=status.HTTP_200_OK)
async def get_audit_log(
    audit_log_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_permissions("audit.read")),
) -> AuditLogRead:
    service = get_audit_service(session)
    audit_log = await service.get_audit_log(audit_log_id)
    if audit_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found.")
    return AuditLogRead.model_validate(audit_log)
