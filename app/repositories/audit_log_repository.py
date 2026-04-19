from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AuditLog


class AuditLogRepository:
    """Handles database access for audit log entries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        actor_user_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: UUID | None,
        status_code: int,
        details: dict | None,
    ) -> AuditLog:
        audit_log = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status_code=status_code,
            details=details,
        )
        self._session.add(audit_log)
        await self._session.flush()
        return audit_log

    async def get_by_id(self, audit_log_id: UUID) -> AuditLog | None:
        result = await self._session.execute(
            select(AuditLog)
            .options(selectinload(AuditLog.actor_user))
            .where(AuditLog.id == audit_log_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        *,
        actor_user_id: UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        query = select(AuditLog).options(selectinload(AuditLog.actor_user))

        if actor_user_id is not None:
            query = query.where(AuditLog.actor_user_id == actor_user_id)
        if action is not None:
            query = query.where(AuditLog.action == action)
        if resource_type is not None:
            query = query.where(AuditLog.resource_type == resource_type)
        if resource_id is not None:
            query = query.where(AuditLog.resource_id == resource_id)
        if date_from is not None:
            query = query.where(AuditLog.created_at >= date_from)
        if date_to is not None:
            query = query.where(AuditLog.created_at <= date_to)

        result = await self._session.execute(query.order_by(AuditLog.created_at.desc()).limit(limit))
        return list(result.scalars().all())
