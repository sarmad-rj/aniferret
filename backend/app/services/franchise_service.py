from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.franchise import Franchise
from app.models.franchise_entry import FranchiseEntry
from app.schemas.franchise import FranchiseEntryRead, WatchOrderResponse


class FranchiseNotFoundError(ValueError):
    """Raised when no Franchise matches the requested slug."""


async def get_watch_order(db: AsyncSession, franchise_slug: str) -> WatchOrderResponse:
    """Assemble the release-order and chronological-order entry list for a franchise."""
    stmt = (
        select(Franchise)
        .where(Franchise.slug == franchise_slug)
        .options(selectinload(Franchise.entries).selectinload(FranchiseEntry.anime))
    )
    result = await db.execute(stmt)
    franchise = result.scalar_one_or_none()
    if franchise is None:
        raise FranchiseNotFoundError(f"No franchise found with slug {franchise_slug!r}")

    entries = [
        FranchiseEntryRead(
            id=entry.id,
            title=entry.title,
            entry_type=entry.entry_type,
            release_order=entry.release_order,
            chronological_order=entry.chronological_order,
            note=entry.note,
            anime_slug=entry.anime.slug if entry.anime else None,
        )
        for entry in sorted(franchise.entries, key=lambda entry: entry.release_order)
    ]

    return WatchOrderResponse(
        franchise_slug=franchise.slug,
        franchise_name=franchise.name,
        entries=entries,
    )
