from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.anime_external_metadata import AnimeExternalMetadata
from app.schemas.external_metadata import AnimeSourcesResponse, ExternalMetadataRead, SourceConflict
from app.services.dossier_service import AnimeNotFoundError, get_anime_by_slug
from app.services.ingestion_service import detect_conflicts

router = APIRouter(tags=["sources"])


@router.get(
    "/anime/{anime_slug}/sources",
    response_model=AnimeSourcesResponse,
    status_code=status.HTTP_200_OK,
)
async def get_anime_sources(
    anime_slug: str, db: AsyncSession = Depends(get_db)
) -> AnimeSourcesResponse:
    """Return per-provider metadata snapshots and any conflicts against curated data (SPEC.md D6)."""
    try:
        anime = await get_anime_by_slug(db, anime_slug)
    except AnimeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc

    result = await db.execute(
        select(AnimeExternalMetadata).where(AnimeExternalMetadata.anime_id == anime.id)
    )
    external_records = list(result.scalars().all())
    conflicts = detect_conflicts(anime, external_records)

    curated_record = ExternalMetadataRead(
        source="aniferret", title=anime.title, episodes=anime.total_episodes
    )
    provider_records = [ExternalMetadataRead.model_validate(record) for record in external_records]

    return AnimeSourcesResponse(
        anime_slug=anime_slug,
        records=[curated_record, *provider_records],
        conflicts=[SourceConflict(**conflict) for conflict in conflicts],
    )
