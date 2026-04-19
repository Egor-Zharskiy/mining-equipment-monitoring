from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_log_repository import AuditLogRepository
from app.services.audit_service import AuditService


def get_audit_service(session: AsyncSession) -> AuditService:
    """Build the audit service for endpoint-side action logging."""

    return AuditService(AuditLogRepository(session))
