from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class SearchItemRead(BaseModel):
    """A compact search result item returned by the global search API."""

    id: UUID
    entity_type: Literal["equipment", "event", "maintenance_task", "user"]
    title: str
    subtitle: str | None = None
    description: str | None = None


class SearchResponse(BaseModel):
    """Grouped global search results for the current user."""

    query: str
    equipment: list[SearchItemRead] = Field(default_factory=list)
    events: list[SearchItemRead] = Field(default_factory=list)
    maintenance_tasks: list[SearchItemRead] = Field(default_factory=list)
    users: list[SearchItemRead] = Field(default_factory=list)
