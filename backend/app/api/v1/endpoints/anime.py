from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.anime import Anime
from app.schemas.anime import AnimeRead
from app.schemas.import_anime import AnimeImportRequest
from app.services.ingestion_service import AnimeImportError, import_anime

router = APIRouter(tags=["anime"])


@router.get("/anime", response_model=list[AnimeRead], status_code=status.HTTP_200_OK)
async def list_anime(db: AsyncSession = Depends(get_db)) -> list[Anime]:
    """List all tracked anime series."""
    result = await db.execute(select(Anime).order_by(Anime.title))
    return list(result.scalars().all())


@router.post("/anime/import", response_model=AnimeRead, status_code=status.HTTP_201_CREATED)
async def import_anime_endpoint(
    payload: AnimeImportRequest, db: AsyncSession = Depends(get_db)
) -> Anime:
    """Dynamically ingest a new anime by title or MAL id: metadata, roster, Gemini-extracted
    Temporal Facts, and vector indexing, end to end. Idempotent — importing an already-known
    anime returns the existing record rather than duplicating it."""
    try:
        return await import_anime(db, payload.query)
    except AnimeImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc
