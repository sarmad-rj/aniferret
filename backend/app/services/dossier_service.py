from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.anime import Anime
from app.schemas.dossier import (
    CharacterDossierEntry,
    DossierResponse,
    FactionDossierEntry,
    RevealedFact,
)
from app.services.reveal_engine import filter_visible_facts, is_revealed


class AnimeNotFoundError(ValueError):
    """Raised when no Anime matches the requested slug."""


async def get_anime_by_slug(db: AsyncSession, slug: str) -> Anime:
    stmt = (
        select(Anime)
        .where(Anime.slug == slug)
        .options(
            selectinload(Anime.characters),
            selectinload(Anime.factions),
            selectinload(Anime.facts),
        )
    )
    result = await db.execute(stmt)
    anime = result.scalar_one_or_none()
    if anime is None:
        raise AnimeNotFoundError(f"No anime found with slug {slug!r}")
    return anime


async def build_dossier(db: AsyncSession, slug: str, checkpoint: str) -> DossierResponse:
    """Assemble a progress-gated character/faction dossier for the given checkpoint."""
    anime = await get_anime_by_slug(db, slug)

    visible_facts = filter_visible_facts(anime.facts, checkpoint)
    locked_facts_count = len(anime.facts) - len(visible_facts)

    facts_by_subject: dict[str, list[RevealedFact]] = {}
    for fact in visible_facts:
        facts_by_subject.setdefault(fact.subject, []).append(RevealedFact.model_validate(fact))

    characters = []
    for character in anime.characters:
        character_revealed = is_revealed(character.first_revealed_at, checkpoint)
        characters.append(
            CharacterDossierEntry(
                id=character.id,
                name=character.name,
                faction_id=character.faction_id,
                role=character.role,
                height=character.height,
                avatar_url=character.avatar_url,
                is_revealed=character_revealed,
                first_revealed_at=character.first_revealed_at,
                bounty=character.bounty if character_revealed else None,
                power=character.power if character_revealed else None,
                backstory=character.backstory if character_revealed else None,
                revealed_facts=facts_by_subject.get(character.name, []),
            )
        )
    factions = [
        FactionDossierEntry(
            id=faction.id,
            name=faction.name,
            description=faction.description,
            parent_id=faction.parent_id,
            revealed_facts=facts_by_subject.get(faction.name, []),
        )
        for faction in anime.factions
    ]

    return DossierResponse(
        anime_id=anime.id,
        anime_slug=anime.slug,
        anime_title=anime.title,
        checkpoint=checkpoint,
        characters=characters,
        factions=factions,
        locked_facts_count=locked_facts_count,
    )
