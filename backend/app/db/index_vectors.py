"""Index all seeded Temporal Facts into ChromaDB for semantic retrieval.

Run with: python -m app.db.index_vectors (after `alembic upgrade head` + seeding).
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models import Anime
from app.services.vector_store import index_facts


async def index_all() -> int:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Anime).options(selectinload(Anime.facts)))
        animes = result.scalars().all()

        pairs = [(fact, anime.slug) for anime in animes for fact in anime.facts]
        index_facts(pairs)
        return len(pairs)


async def main() -> None:
    count = await index_all()
    print(f"Indexed {count} facts into ChromaDB.")


if __name__ == "__main__":
    asyncio.run(main())
