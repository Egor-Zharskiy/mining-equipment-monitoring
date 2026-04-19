from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Equipment, Parameter, TelemetryEvaluation, TelemetryReading, ThresholdRule


class TelemetryEvaluationRepository:
    """Handles database access for telemetry evaluation entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the active asynchronous database session."""

        self._session = session

    async def create(
        self,
        *,
        telemetry_reading: TelemetryReading,
        equipment: Equipment,
        parameter: Parameter,
        threshold_rule: ThresholdRule | None,
        status: str,
    ) -> TelemetryEvaluation:
        """Persist a telemetry evaluation for a reading."""

        evaluation = TelemetryEvaluation(
            telemetry_reading=telemetry_reading,
            equipment=equipment,
            parameter=parameter,
            threshold_rule=threshold_rule,
            status=status,
        )
        self._session.add(evaluation)
        await self._session.flush()
        await self._session.refresh(evaluation)
        return await self.get_by_reading_id(telemetry_reading.id)  # type: ignore[return-value]

    async def get_by_reading_id(self, telemetry_reading_id: UUID) -> TelemetryEvaluation | None:
        """Return an evaluation by telemetry reading identifier."""

        result = await self._session.execute(
            select(TelemetryEvaluation)
            .options(
                selectinload(TelemetryEvaluation.telemetry_reading),
                selectinload(TelemetryEvaluation.threshold_rule),
            )
            .where(TelemetryEvaluation.telemetry_reading_id == telemetry_reading_id)
        )
        return result.scalar_one_or_none()
