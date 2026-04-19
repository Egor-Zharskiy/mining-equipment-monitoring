from app.repositories.search_repository import SearchRepository
from app.schemas.search import SearchItemRead, SearchResponse


class SearchService:
    """Encapsulates permission-aware global search logic."""

    def __init__(self, search_repository: SearchRepository) -> None:
        self._search_repository = search_repository

    async def search(self, *, query: str, current_user, limit_per_section: int) -> SearchResponse:
        permission_codes = {
            permission.code
            for role in current_user.roles
            for permission in role.permissions
        }

        equipment = []
        if "equipment.read" in permission_codes:
            equipment_rows = await self._search_repository.search_equipment(query, limit=limit_per_section)
            equipment = [
                SearchItemRead(
                    id=row["id"],
                    entity_type="equipment",
                    title=row["name"],
                    subtitle=f'{row["code"]} • {row["location"]}',
                    description=row["equipment_type_name"],
                )
                for row in equipment_rows
            ]

        events = []
        if "events.read" in permission_codes:
            event_rows = await self._search_repository.search_events(query, limit=limit_per_section)
            events = [
                SearchItemRead(
                    id=row["id"],
                    entity_type="event",
                    title=row["title"],
                    subtitle=f'{row["equipment_name"]} • {row["severity"]}',
                    description=row["message"],
                )
                for row in event_rows
            ]

        maintenance_tasks = []
        if "maintenance.read" in permission_codes:
            task_rows = await self._search_repository.search_maintenance_tasks(query, limit=limit_per_section)
            maintenance_tasks = [
                SearchItemRead(
                    id=row["id"],
                    entity_type="maintenance_task",
                    title=row["title"],
                    subtitle=f'{row["equipment_code"]} • {row["equipment_name"]}',
                    description=row["description"] or row["status"],
                )
                for row in task_rows
            ]

        users = []
        if "users.read" in permission_codes:
            user_rows = await self._search_repository.search_users(query, limit=limit_per_section)
            users = [
                SearchItemRead(
                    id=row["id"],
                    entity_type="user",
                    title=f'{row["first_name"]} {row["last_name"]}'.strip() or row["username"],
                    subtitle=f'@{row["username"]} • {row["email"]}',
                    description="Активен" if row["is_active"] else "Неактивен",
                )
                for row in user_rows
            ]

        return SearchResponse(
            query=query,
            equipment=equipment,
            events=events,
            maintenance_tasks=maintenance_tasks,
            users=users,
        )
