from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.query import QueryRequest, QueryResponse
from app.services.dossier_service import AnimeNotFoundError
from app.services.query_service import answer_query

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def post_query(
    payload: QueryRequest, db: AsyncSession = Depends(get_db)
) -> QueryResponse:
    """Answer a lore question, gated by the reveal engine with a uniform refusal fallback."""
    try:
        return await answer_query(db, payload.anime_slug, payload.checkpoint, payload.question)
    except AnimeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc
