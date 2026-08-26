from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.anime import Anime
from app.schemas.anime import AnimeRead

router = APIRouter(tags=["anime"])


@router.get("/anime", response_model=list[AnimeRead], status_code=status.HTTP_200_OK)
async def list_anime(db: AsyncSession = Depends(get_db)) -> list[Anime]:
    """List all tracked anime series."""
    result = await db.execute(select(Anime).order_by(Anime.title))
    return list(result.scalars().all())
