from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.maintenance import MaintenanceUserRead


class AuditLogRead(BaseModel):
    """Audit log representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_user: MaintenanceUserRead | None
    action: str
    resource_type: str
    resource_id: UUID | None
    status_code: int
    details: dict[str, Any] | None
    created_at: datetime
