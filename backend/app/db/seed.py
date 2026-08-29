"""Seed dataset for the launch corpus: Classroom of the Elite, Code Geass, and Attack on Titan.

Run with: python -m app.db.seed (requires migrations applied via `alembic upgrade head`).

mal_id/anilist_id are real, verified IDs (cross-checked live against both APIs) — they drive
external metadata ingestion (app/db/ingest_sources.py, SPEC.md D6).
"""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models import Anime, Character, Faction, TemporalFact
from app.services.ingestion_service import fetch_character_roster, ingest_character_roster

logger = logging.getLogger(__name__)

SEED_ANIME: list[dict] = [
    {
        "slug": "classroom-of-the-elite",
        "title": "Classroom of the Elite",
        "total_episodes": 37,
        "season_episode_counts": [12, 13, 12],
        "mal_id": 35507,
        "anilist_id": 98659,
        "factions": [
            {
                "name": "Class D",
                "description": "The lowest-ranked class at the Advanced Nurturing High School.",
            },
        ],
        "characters": [
            {"name": "Kiyotaka Ayanokoji", "faction": "Class D"},
            {"name": "Suzune Horikita", "faction": "Class D"},
            {"name": "Kikyo Kushida", "faction": "Class D"},
        ],
        "facts": [
            {
                "subject": "Class D",
                "predicate": "point_system",
                "object": "Students accumulate class points that convert into personal spending points, and a class's points can drop to zero.",
                "source_citation": "Season 1, Episode 1",
                "first_revealed_at": "S1E1",
                "first_hinted_at": None,
                "confidence": 0.99,
            },
            {
                "subject": "Kikyo Kushida",
                "predicate": "true_personality",
                "object": "Conceals a manipulative, ruthless personality behind a friendly public facade.",
                "source_citation": "Season 1, Episode 11",
                "first_revealed_at": "S1E11",
                "first_hinted_at": "S1E4",
                "confidence": 0.92,
            },
            {
                "subject": "Kiyotaka Ayanokoji",
                "predicate": "hidden_ability",
                "object": "Trained under an elite program with exceptional analytical and combat skills, deliberately suppressed to appear average.",
                "source_citation": "Season 1, Episode 12",
                "first_revealed_at": "S1E12",
                "first_hinted_at": "S1E2",
                "confidence": 0.9,
            },
        ],
    },
    {
        "slug": "code-geass",
        "title": "Code Geass",
        "total_episodes": 50,
        "season_episode_counts": [25, 25],
        "mal_id": 1575,
        "anilist_id": 1575,
        "factions": [
            {
                "name": "Holy Britannian Empire",
                "description": "The ruling imperial power occupying Area 11.",
            },
            {
                "name": "Black Knights",
                "description": "A resistance organization opposing Britannian rule.",
            },
        ],
        "characters": [
            {"name": "Lelouch Lamperouge", "faction": "Holy Britannian Empire"},
            {"name": "Suzaku Kururugi", "faction": "Holy Britannian Empire"},
            {"name": "Kallen Kouzuki", "faction": "Black Knights"},
            {"name": "C.C.", "faction": None},
        ],
        "facts": [
            {
                "subject": "Lelouch Lamperouge",
                "predicate": "royal_lineage",
                "object": "11th prince of the Holy Britannian Empire, living in exile.",
                "source_citation": "Season 1, Episode 1",
                "first_revealed_at": "S1E1",
                "first_hinted_at": None,
                "confidence": 0.99,
            },
            {
                "subject": "C.C.",
                "predicate": "power_source",
                "object": "Grants Lelouch the power of Geass: absolute obedience over anyone he commands.",
                "source_citation": "Season 1, Episode 1",
                "first_revealed_at": "S1E1",
                "first_hinted_at": None,
                "confidence": 0.95,
            },
            {
                "subject": "Lelouch Lamperouge",
                "predicate": "true_identity",
                "object": "Zero, masked leader of the Black Knights.",
                "source_citation": "Season 1, Episode 12",
                "first_revealed_at": "S1E12",
                "first_hinted_at": "S1E3",
                "confidence": 0.97,
            },
        ],
    },
    {
        "slug": "attack-on-titan",
        "title": "Attack on Titan",
        "total_episodes": 25,
        "season_episode_counts": [25],
        "mal_id": 16498,
        "anilist_id": 16498,
        "factions": [
            {
                "name": "Survey Corps",
                "description": "Ventures beyond the walls to battle Titans and reclaim lost territory.",
            },
            {
                "name": "Garrison",
                "description": "Maintains and defends the walls that protect humanity's remaining territory.",
            },
            {
                "name": "Military Police Brigade",
                "description": "Maintains order within the innermost wall and serves the royal government.",
            },
            {
                "name": "104th Cadet Corps",
                "description": "The training regiment cadets join before choosing a military branch.",
            },
        ],
        "characters": [
            {"name": "Eren Yeager", "faction": "104th Cadet Corps"},
            {"name": "Mikasa Ackerman", "faction": "104th Cadet Corps"},
            {"name": "Armin Arlert", "faction": "104th Cadet Corps"},
            {"name": "Annie Leonhart", "faction": "104th Cadet Corps"},
            {"name": "Levi Ackerman", "faction": "Survey Corps"},
            {"name": "Erwin Smith", "faction": "Survey Corps"},
        ],
        "facts": [
            {
                "subject": "104th Cadet Corps",
                "predicate": "training_purpose",
                "object": "Cadets train together for years before choosing a branch: Survey Corps, Garrison, or Military Police Brigade.",
                "source_citation": "Season 1, Episode 1",
                "first_revealed_at": "S1E1",
                "first_hinted_at": None,
                "confidence": 0.99,
            },
            {
                "subject": "Levi Ackerman",
                "predicate": "military_rank",
                "object": "Captain of the Survey Corps, renowned as humanity's strongest soldier.",
                "source_citation": "Season 1, Episode 14",
                "first_revealed_at": "S1E14",
                "first_hinted_at": None,
                "confidence": 0.95,
            },
            {
                "subject": "Eren Yeager",
                "predicate": "titan_shifter_identity",
                "object": "Can transform into a Titan himself, discovered after emerging from within a Titan's body.",
                "source_citation": "Season 1, Episode 8",
                "first_revealed_at": "S1E8",
                "first_hinted_at": "S1E5",
                "confidence": 0.96,
            },
            {
                "subject": "Eren Yeager",
                "predicate": "basement_lore",
                "object": "His father Grisha left behind a hidden basement holding the truth about the Titans and the world beyond the walls.",
                "source_citation": "Season 1, Episode 25",
                "first_revealed_at": "S1E25",
                "first_hinted_at": "S1E13",
                "confidence": 0.93,
            },
            {
                "subject": "Annie Leonhart",
                "predicate": "titan_shifter_identity",
                "object": "Secretly the Female Titan that attacked the Survey Corps during the 57th expedition beyond the walls.",
                "source_citation": "Season 1, Episode 25",
                "first_revealed_at": "S1E25",
                "first_hinted_at": "S1E17",
                "confidence": 0.9,
            },
        ],
    },
    {
        "slug": "one-piece",
        "title": "One Piece",
        "total_episodes": 1120,
        # A single continuous season: the Watch Progress slider represents plain
        # sequential episode numbers (Ep. 1 -> Ep. 1120) rather than per-arc season
        # boundaries. Checkpoints below ("S1E<n>") use n as that raw global episode
        # number directly.
        "season_episode_counts": [1120],
        "mal_id": 21,
        "anilist_id": 21,
        # Deliberately no "factions" or "characters" keys here: per SPEC.md's Faction
        # architecture, One Piece's roster and Pirate-Crews/Marines/Warlords/Yonko/
        # Revolutionary-Army hierarchy are ingested dynamically via _seed_dynamic_roster
        # below (AniList roster fetch -> app/services/faction_classifier.py
        # classification), not hand-authored here. It degrades to zero characters/
        # factions (anime + curated facts still seed fine) if AniList is unreachable.
        "dynamic_roster_mal_id": 21,
        "dynamic_roster_limit": 40,
        "facts": [
            {
                "subject": "Monkey D. Luffy",
                "predicate": "devil_fruit_power",
                "object": "Ate the Gomu Gomu no Mi, granting him a rubber body.",
                "source_citation": "Episode 1",
                "first_revealed_at": "S1E1",
                "first_hinted_at": "S1E1",
                "confidence": 0.99,
            },
            {
                "subject": "Monkey D. Luffy",
                "predicate": "combat_technique",
                "object": "Developed Gear Second, pumping blood at high speed for a burst of speed and striking power.",
                "source_citation": "Episode 581",
                "first_revealed_at": "S1E581",
                "first_hinted_at": "S1E580",
                "confidence": 0.95,
            },
            {
                "subject": "Roronoa Zoro",
                "predicate": "combat_style",
                "object": "Master of Santoryu, the Three-Sword Style.",
                "source_citation": "Episode 2",
                "first_revealed_at": "S1E2",
                "first_hinted_at": "S1E2",
                "confidence": 0.98,
            },
            {
                "subject": "Nami",
                "predicate": "true_loyalty",
                "object": "Secretly worked for the Arlong Pirates only to earn enough money to buy back Cocoyasi Village's freedom.",
                "source_citation": "Episode 37",
                "first_revealed_at": "S1E37",
                "first_hinted_at": "S1E31",
                "confidence": 0.94,
            },
            {
                "subject": "Nico Robin",
                "predicate": "secret_identity",
                "object": "Operates as Miss All Sunday, Crocodile's partner within Baroque Works.",
                "source_citation": "Episode 128",
                "first_revealed_at": "S1E128",
                "first_hinted_at": "S1E128",
                "confidence": 0.93,
            },
            {
                "subject": "Nico Robin",
                "predicate": "crew_membership",
                "object": "Joins the Straw Hat Pirates as their archaeologist after the Alabasta incident.",
                "source_citation": "Episode 296",
                "first_revealed_at": "S1E296",
                "first_hinted_at": "S1E296",
                "confidence": 0.97,
            },
            {
                "subject": "Crocodile",
                "predicate": "true_identity",
                "object": "A former Warlord of the Sea secretly leading Baroque Works' Operation Utopia to seize Alabasta.",
                "source_citation": "Episode 272",
                "first_revealed_at": "S1E272",
                "first_hinted_at": "S1E137",
                "confidence": 0.92,
            },
            {
                "subject": "Portgas D. Ace",
                "predicate": "true_lineage",
                "object": "Biological son of the Pirate King, Gol D. Roger, and Luffy's sworn brother.",
                "source_citation": "Episode 770",
                "first_revealed_at": "S1E770",
                "first_hinted_at": "S1E152",
                "confidence": 0.9,
            },
        ],
    },
]


async def _seed_dynamic_roster(session: AsyncSession, anime: Anime, mal_id: int, limit: int) -> None:
    """Best-effort dynamic character/faction ingestion for a launch-corpus anime that
    intentionally ships with no hardcoded character dictionary. Mirrors the ingestion
    pipeline's own graceful-degradation contract (app/services/ingestion_service.py):
    any network or extraction failure leaves the anime seeded with zero characters
    rather than aborting the whole seed run.
    """
    try:
        roster = await fetch_character_roster(mal_id, limit=limit)
        if not roster:
            logger.warning("No dynamic roster returned for %r; seeding without characters.", anime.slug)
            return
        await ingest_character_roster(session, anime, roster)
    except Exception:
        logger.warning("Dynamic roster ingestion failed for %r.", anime.slug, exc_info=True)


async def seed_all(session: AsyncSession) -> None:
    """Idempotently insert the launch corpus. Skips any anime whose slug already exists."""
    for anime_data in SEED_ANIME:
        existing = await session.execute(select(Anime).where(Anime.slug == anime_data["slug"]))
        if existing.scalar_one_or_none() is not None:
            continue

        anime = Anime(
            slug=anime_data["slug"],
            title=anime_data["title"],
            total_episodes=anime_data["total_episodes"],
            season_episode_counts=anime_data["season_episode_counts"],
            mal_id=anime_data.get("mal_id"),
            anilist_id=anime_data.get("anilist_id"),
        )
        session.add(anime)
        await session.flush()

        faction_by_name: dict[str, Faction] = {}
        for faction_data in anime_data.get("factions", []):
            faction = Faction(
                anime_id=anime.id,
                name=faction_data["name"],
                description=faction_data.get("description"),
            )
            session.add(faction)
            faction_by_name[faction_data["name"]] = faction
        await session.flush()

        for character_data in anime_data.get("characters", []):
            faction = faction_by_name.get(character_data.get("faction"))
            session.add(
                Character(
                    anime_id=anime.id,
                    name=character_data["name"],
                    faction_id=faction.id if faction else None,
                )
            )

        for fact_data in anime_data["facts"]:
            session.add(TemporalFact(anime_id=anime.id, **fact_data))

        dynamic_mal_id = anime_data.get("dynamic_roster_mal_id")
        if dynamic_mal_id is not None:
            await session.flush()
            await _seed_dynamic_roster(
                session, anime, dynamic_mal_id, anime_data.get("dynamic_roster_limit", 8)
            )

    await session.commit()


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await seed_all(session)


if __name__ == "__main__":
    asyncio.run(main())
