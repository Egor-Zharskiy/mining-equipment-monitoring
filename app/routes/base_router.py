from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_async_session

router = APIRouter(prefix="")


@router.get("/")
async def main(db: AsyncSession = Depends(get_async_session)):
    return {"message": "Hello World"}
