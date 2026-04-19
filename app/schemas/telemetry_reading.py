from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.equipment import EquipmentRead
from app.schemas.parameter import ParameterRead


class TelemetryEvaluationRead(BaseModel):
    """Evaluation result of a telemetry reading against threshold rules."""

    model_config = ConfigDict(from_attributes=True)

    status: str
    threshold_rule_id: UUID | None
    created_at: datetime


class TelemetryReadingCreate(BaseModel):
    """Payload used to create a telemetry reading."""

    equipment_id: UUID
    parameter_id: UUID
    value: Decimal = Field(max_digits=14, decimal_places=4)
    measured_at: datetime


class TelemetryReadingRead(BaseModel):
    """Telemetry reading representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    equipment: EquipmentRead
    parameter: ParameterRead
    value: Decimal
    measured_at: datetime
    received_at: datetime
    evaluation: TelemetryEvaluationRead | None = None
