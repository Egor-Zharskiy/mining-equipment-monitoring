import logging
from datetime import datetime
from uuid import UUID

from app.repositories.audit_log_repository import AuditLogRepository

SENSITIVE_AUDIT_FIELDS = {"password", "hashed_password", "access_token", "refresh_token", "token"}

logger = logging.getLogger(__name__)


class AuditService:
    """Encapsulates audit log creation and querying."""

    def __init__(
        self,
        audit_log_repository: AuditLogRepository,
    ) -> None:
        self._audit_log_repository = audit_log_repository

    async def log_action(
        self,
        *,
        actor_user_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: UUID | None,
        status_code: int,
        details: dict | None = None,
    ):
        sanitized_details = self._sanitize(details)
        audit_log = await self._audit_log_repository.create(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status_code=status_code,
            details=sanitized_details,
        )
        logger.info(
            "audit_log_created",
            extra={
                "audit_log_id": str(audit_log.id),
                "actor_user_id": str(actor_user_id) if actor_user_id else None,
                "action": action,
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id else None,
                "status_code": status_code,
            },
        )
        return audit_log

    async def list_audit_logs(
        self,
        *,
        actor_user_id: UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 100,
    ):
        self._validate_date_range(date_from=date_from, date_to=date_to)

        return await self._audit_log_repository.list_all(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )

    async def get_audit_log(self, audit_log_id: UUID):
        return await self._audit_log_repository.get_by_id(audit_log_id)

    @classmethod
    def build_details(
        cls,
        *,
        request_data: dict | None = None,
        extra: dict | None = None,
    ) -> dict | None:
        payload: dict = {}
        if request_data:
            payload["request"] = cls._sanitize(request_data)
        if extra:
            payload["extra"] = cls._sanitize(extra)
        return payload or None

    @staticmethod
    def _validate_date_range(*, date_from: datetime | None, date_to: datetime | None) -> None:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise ValueError("Invalid date range: date_from must be less than or equal to date_to.")

    @classmethod
    def _sanitize(cls, value):
        if isinstance(value, dict):
            sanitized: dict = {}
            for key, nested_value in value.items():
                if key.lower() in SENSITIVE_AUDIT_FIELDS:
                    sanitized[key] = "***"
                else:
                    sanitized[key] = cls._sanitize(nested_value)
            return sanitized
        if isinstance(value, list):
            return [cls._sanitize(item) for item in value]
        return value
