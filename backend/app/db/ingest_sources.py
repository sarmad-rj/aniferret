"""Ingest external metadata for all seeded anime with a known MAL id (SPEC.md D6).

Run with: python -m app.db.ingest_sources (after seeding). Requires network access to
api.jikan.moe and graphql.anilist.co.
"""

import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models import Anime
from app.services.ingestion_service import ingest_anime_sources


async def ingest_all() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Anime))
        animes = result.scalars().all()

        for anime in animes:
            records = await ingest_anime_sources(session, anime)
            print(f"{anime.slug}: ingested {len(records)} source record(s)")


if __name__ == "__main__":
    asyncio.run(ingest_all())
