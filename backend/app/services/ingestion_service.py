"""External metadata ingestion from Jikan REST v4 and AniList GraphQL (SPEC.md D6).

Ingestion is a deliberate, on-demand operation (run via app/db/ingest_sources.py), never
triggered on the request path — external providers are slow/rate-limited/occasionally
unavailable, and a dossier read must never depend on their uptime.

Both providers are queried by MAL id: Jikan's own search endpoint is flaky upstream, but
its by-id lookup is reliable, and AniList's schema accepts an `idMal` argument directly —
so a single MAL id is enough to look up both, without needing AniList's separate ID space.
"""

import httpx
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.anime import Anime
from app.models.anime_external_metadata import AnimeExternalMetadata

_TIMEOUT = 15.0
_ANILIST_URL = "https://graphql.anilist.co"
_ANILIST_QUERY = """
query ($idMal: Int) {
  Media(idMal: $idMal, type: ANIME) {
    title { romaji }
    episodes
    averageScore
    description(asHtml: false)
  }
}
"""


async def fetch_jikan_metadata(mal_id: int) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"https://api.jikan.moe/v4/anime/{mal_id}")
            response.raise_for_status()
    except httpx.HTTPError:
        return None

    data = response.json().get("data")
    if not data:
        return None

    return {
        "title": data.get("title"),
        "episodes": data.get("episodes"),
        "score": data.get("score"),
        "synopsis": data.get("synopsis"),
    }


async def fetch_anilist_metadata(mal_id: int) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                _ANILIST_URL, json={"query": _ANILIST_QUERY, "variables": {"idMal": mal_id}}
            )
            response.raise_for_status()
    except httpx.HTTPError:
        return None

    media = (response.json().get("data") or {}).get("Media")
    if not media:
        return None

    average_score = media.get("averageScore")
    return {
        "title": (media.get("title") or {}).get("romaji"),
        "episodes": media.get("episodes"),
        "score": (average_score / 10) if average_score is not None else None,
        "synopsis": media.get("description"),
    }


async def ingest_anime_sources(session: AsyncSession, anime: Anime) -> list[AnimeExternalMetadata]:
    """Fetch and store Jikan + AniList snapshots for one anime.

    Skips entirely if the anime has no mal_id on file. A source that fails or times out
    is simply omitted from the result — a slow provider must never fail the whole ingest.
    """
    if anime.mal_id is None:
        return []

    await session.execute(
        delete(AnimeExternalMetadata).where(AnimeExternalMetadata.anime_id == anime.id)
    )

    records: list[AnimeExternalMetadata] = []

    jikan_data = await fetch_jikan_metadata(anime.mal_id)
    if jikan_data:
        records.append(AnimeExternalMetadata(anime_id=anime.id, source="jikan", **jikan_data))

    anilist_data = await fetch_anilist_metadata(anime.mal_id)
    if anilist_data:
        records.append(AnimeExternalMetadata(anime_id=anime.id, source="anilist", **anilist_data))

    session.add_all(records)
    await session.commit()
    for record in records:
        await session.refresh(record)
    return records


def detect_conflicts(anime: Anime, records: list[AnimeExternalMetadata]) -> list[dict]:
    """Surface fields where AniFerret's curated data and external providers disagree.

    Note: providers commonly disagree on 'episodes' for multi-season franchises because
    AniList/MAL list each season as a separate entry, while AniFerret's total_episodes is
    the combined count across all tracked seasons — that's a genuine, expected conflict
    worth surfacing, not a data bug.
    """
    conflicts: list[dict] = []

    episode_values: dict[str, int | None] = {"aniferret": anime.total_episodes}
    for record in records:
        if record.episodes is not None:
            episode_values[record.source] = record.episodes
    if len(set(episode_values.values())) > 1:
        conflicts.append({"field": "episodes", "values": episode_values})

    title_values: dict[str, str | None] = {"aniferret": anime.title}
    for record in records:
        if record.title:
            title_values[record.source] = record.title
    if len(set(title_values.values())) > 1:
        conflicts.append({"field": "title", "values": title_values})

    return conflicts
