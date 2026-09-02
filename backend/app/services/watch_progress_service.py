from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.anime import Anime
from app.models.watch_progress import WatchProgress
from app.schemas.watch_progress import WatchProgressEntry, WatchProgressResponse


async def get_watch_progress(db: AsyncSession, user_id: int) -> WatchProgressResponse:
    stmt = (
        select(WatchProgress)
        .where(WatchProgress.user_id == user_id)
        .options(selectinload(WatchProgress.anime))
    )
    result = await db.execute(stmt)
    entries = [
        WatchProgressEntry(anime_slug=progress.anime.slug, checkpoint=progress.checkpoint)
        for progress in result.scalars().all()
    ]
    return WatchProgressResponse(entries=entries)


class UnknownAnimeSlugError(ValueError):
    """Raised when an upsert references a slug with no matching Anime row."""


async def upsert_watch_progress(
    db: AsyncSession, user_id: int, entries: list[WatchProgressEntry]
) -> WatchProgressResponse:
    """Upsert each (user, anime) -> checkpoint pair. Serves both a single-entry "save my
    current position" call and a multi-entry "bulk-sync my guest progress on login" call
    through the same endpoint."""
    slugs = {entry.anime_slug for entry in entries}
    result = await db.execute(select(Anime).where(Anime.slug.in_(slugs)))
    anime_by_slug = {anime.slug: anime for anime in result.scalars().all()}

    unknown = slugs - anime_by_slug.keys()
    if unknown:
        raise UnknownAnimeSlugError(f"Unknown anime slug(s): {', '.join(sorted(unknown))}")

    existing_result = await db.execute(
        select(WatchProgress).where(
            WatchProgress.user_id == user_id,
            WatchProgress.anime_id.in_(anime.id for anime in anime_by_slug.values()),
        )
    )
    existing_by_anime_id = {
        progress.anime_id: progress for progress in existing_result.scalars().all()
    }

    for entry in entries:
        anime = anime_by_slug[entry.anime_slug]
        existing = existing_by_anime_id.get(anime.id)
        if existing is not None:
            existing.checkpoint = entry.checkpoint
        else:
            db.add(WatchProgress(user_id=user_id, anime_id=anime.id, checkpoint=entry.checkpoint))

    await db.commit()
    return await get_watch_progress(db, user_id)
