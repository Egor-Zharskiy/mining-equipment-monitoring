from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Equipment, EquipmentType, Event, MaintenanceTask, User


class SearchRepository:
    """Provides lightweight column-based queries for global search."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search_equipment(self, query: str, *, limit: int) -> list[dict]:
        pattern = f"%{query}%"
        result = await self._session.execute(
            select(
                Equipment.id,
                Equipment.name,
                Equipment.code,
                Equipment.location,
                EquipmentType.name.label("equipment_type_name"),
            )
            .join(EquipmentType, Equipment.equipment_type_id == EquipmentType.id)
            .where(Equipment.is_active.is_(True))
            .where(
                or_(
                    Equipment.name.ilike(pattern),
                    Equipment.code.ilike(pattern),
                    Equipment.location.ilike(pattern),
                    Equipment.serial_number.ilike(pattern),
                )
            )
            .order_by(Equipment.name.asc())
            .limit(limit)
        )
        return [dict(row._mapping) for row in result.all()]

    async def search_events(self, query: str, *, limit: int) -> list[dict]:
        pattern = f"%{query}%"
        result = await self._session.execute(
            select(
                Event.id,
                Event.title,
                Event.message,
                Event.severity,
                Equipment.name.label("equipment_name"),
                Equipment.code.label("equipment_code"),
            )
            .join(Equipment, Event.equipment_id == Equipment.id)
            .where(
                or_(
                    Event.title.ilike(pattern),
                    Event.message.ilike(pattern),
                    Equipment.name.ilike(pattern),
                    Equipment.code.ilike(pattern),
                )
            )
            .order_by(Event.created_at.desc())
            .limit(limit)
        )
        return [dict(row._mapping) for row in result.all()]

    async def search_maintenance_tasks(self, query: str, *, limit: int) -> list[dict]:
        pattern = f"%{query}%"
        result = await self._session.execute(
            select(
                MaintenanceTask.id,
                MaintenanceTask.title,
                MaintenanceTask.description,
                MaintenanceTask.status,
                Equipment.name.label("equipment_name"),
                Equipment.code.label("equipment_code"),
            )
            .join(Equipment, MaintenanceTask.equipment_id == Equipment.id)
            .where(
                or_(
                    MaintenanceTask.title.ilike(pattern),
                    MaintenanceTask.description.ilike(pattern),
                    Equipment.name.ilike(pattern),
                    Equipment.code.ilike(pattern),
                )
            )
            .order_by(MaintenanceTask.created_at.desc())
            .limit(limit)
        )
        return [dict(row._mapping) for row in result.all()]

    async def search_users(self, query: str, *, limit: int) -> list[dict]:
        pattern = f"%{query}%"
        result = await self._session.execute(
            select(
                User.id,
                User.first_name,
                User.last_name,
                User.username,
                User.email,
                User.is_active,
            )
            .where(
                or_(
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                    User.username.ilike(pattern),
                    User.email.ilike(pattern),
                )
            )
            .order_by(User.last_name.asc(), User.first_name.asc(), User.username.asc())
            .limit(limit)
        )
        return [dict(row._mapping) for row in result.all()]
