from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.equipment import EquipmentRead
from app.schemas.parameter import ParameterRead


class EventRead(BaseModel):
    """Monitoring event representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    equipment: EquipmentRead
    parameter: ParameterRead | None
    telemetry_reading_id: UUID | None
    event_type: str
    severity: str
    title: str
    message: str
    created_at: datetime
