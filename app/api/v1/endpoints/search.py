from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.dependencies.auth import get_current_user
from app.repositories.search_repository import SearchRepository
from app.schemas.search import SearchResponse
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def global_search(
    q: str = Query(min_length=2, max_length=100),
    limit_per_section: int = Query(default=5, ge=1, le=10),
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
) -> SearchResponse:
    """Return grouped search results across entities available to the current user."""

    service = SearchService(SearchRepository(session))
    return await service.search(
        query=q.strip(),
        current_user=current_user,
        limit_per_section=limit_per_section,
    )
