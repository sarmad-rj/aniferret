from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.checkpoint import CHECKPOINT_PATTERN
from app.schemas.dossier import DossierResponse
from app.services.dossier_service import AnimeNotFoundError, build_dossier

router = APIRouter(tags=["dossier"])


@router.get(
    "/dossier/{anime_slug}", response_model=DossierResponse, status_code=status.HTTP_200_OK
)
async def get_dossier(
    anime_slug: str,
    checkpoint: str = Query(..., pattern=CHECKPOINT_PATTERN, description="User's watch checkpoint, e.g. 'S1E10'"),
    db: AsyncSession = Depends(get_db),
) -> DossierResponse:
    """Return a progress-gated character/faction dossier for the given anime and checkpoint."""
    try:
        return await build_dossier(db, anime_slug, checkpoint)
    except AnimeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc
