from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.anime import Anime
from app.models.faction import Faction
from app.schemas.dossier import (
    CharacterDossierEntry,
    DossierResponse,
    FactionDossierEntry,
    RevealedFact,
)
from app.services.reveal_engine import filter_visible_facts, is_revealed, parse_checkpoint

_BOUNTY_PREDICATE = "bounty"


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


def _prune_empty_factions(
    factions: list[Faction],
    characters: list[CharacterDossierEntry],
    facts_by_subject: dict[str, list[RevealedFact]],
) -> list[FactionDossierEntry]:
    """Drop any faction/crew with zero currently-introduced members from the response.

    A top-level faction survives if it has direct members itself OR at least one of its
    nested crews does — so a card like "Pirate Crews" never renders with an empty
    "Straw Hat Pirates" sub-section (or, before anyone in that faction has debuted, at
    all) before the introduction arc for its first member.
    """
    member_counts: dict[int, int] = {}
    for character in characters:
        if character.faction_id is not None:
            member_counts[character.faction_id] = member_counts.get(character.faction_id, 0) + 1

    def has_direct_members(faction_id: int) -> bool:
        return member_counts.get(faction_id, 0) > 0

    children_by_parent: dict[int, list[Faction]] = {}
    for faction in factions:
        if faction.parent_id is not None:
            children_by_parent.setdefault(faction.parent_id, []).append(faction)

    surviving_ids: set[int] = {
        faction.id
        for faction in factions
        if faction.parent_id is not None and has_direct_members(faction.id)
    }
    surviving_ids |= {
        faction.id
        for faction in factions
        if faction.parent_id is None
        and (
            has_direct_members(faction.id)
            or any(child.id in surviving_ids for child in children_by_parent.get(faction.id, []))
        )
    }

    return [
        FactionDossierEntry(
            id=faction.id,
            name=faction.name,
            description=faction.description,
            parent_id=faction.parent_id,
            revealed_facts=facts_by_subject.get(faction.name, []),
        )
        for faction in factions
        if faction.id in surviving_ids
    ]


def _current_bounty(
    static_bounty: str | None,
    character_facts: list[RevealedFact],
    has_bounty_history: bool,
) -> str | None:
    """A bounty isn't a fixed stat — it climbs over the series. If Gemini extracted
    dated 'bounty' facts from the bio's bounty history (see
    _EXTRACTION_SYSTEM_INSTRUCTION), use whichever is most recent as of the checkpoint
    (character_facts is already reveal-gated, so this only ever considers amounts the
    user could already know).

    `static_bounty` (scraped from the bio's single 'Bounty:' line) is always that
    character's *most recent real-world* bounty — for a character with a tracked
    history, falling back to it before their first milestone fact unlocks would leak
    their final/current amount ahead of schedule (e.g. showing a still-unbountied Ep.1
    Luffy's endgame bounty). So it's only used as a fallback for characters who have no
    tracked bounty history at all, where it's just a flat, non-progressive stat.
    """
    bounty_facts = [fact for fact in character_facts if fact.predicate.lower() == _BOUNTY_PREDICATE]
    if bounty_facts:
        latest = max(bounty_facts, key=lambda fact: parse_checkpoint(fact.first_revealed_at))
        return latest.object
    if has_bounty_history:
        return None
    return static_bounty


async def build_dossier(db: AsyncSession, slug: str, checkpoint: str) -> DossierResponse:
    """Assemble a progress-gated character/faction dossier for the given checkpoint."""
    anime = await get_anime_by_slug(db, slug)

    visible_facts = filter_visible_facts(anime.facts, checkpoint)
    locked_facts_count = len(anime.facts) - len(visible_facts)

    facts_by_subject: dict[str, list[RevealedFact]] = {}
    for fact in visible_facts:
        facts_by_subject.setdefault(fact.subject, []).append(RevealedFact.model_validate(fact))

    subjects_with_bounty_history = {
        fact.subject for fact in anime.facts if fact.predicate.lower() == _BOUNTY_PREDICATE
    }

    # Characters not yet introduced (first_revealed_at > checkpoint) are dropped from the
    # response entirely, not merely field-masked — SPEC.md D1's "zero prompt-level spoiler
    # leakage" extends to a character's very existence in the roster, not just their stats.
    characters = []
    for character in anime.characters:
        if not is_revealed(character.first_revealed_at, checkpoint):
            continue
        character_facts = facts_by_subject.get(character.name, [])
        characters.append(
            CharacterDossierEntry(
                id=character.id,
                name=character.name,
                faction_id=character.faction_id,
                role=character.role,
                height=character.height,
                avatar_url=character.avatar_url,
                is_revealed=True,
                first_revealed_at=character.first_revealed_at,
                bounty=_current_bounty(
                    character.bounty,
                    character_facts,
                    character.name in subjects_with_bounty_history,
                ),
                power=character.power,
                backstory=character.backstory,
                revealed_facts=character_facts,
            )
        )
    factions = _prune_empty_factions(anime.factions, characters, facts_by_subject)

    return DossierResponse(
        anime_id=anime.id,
        anime_slug=anime.slug,
        anime_title=anime.title,
        checkpoint=checkpoint,
        characters=characters,
        factions=factions,
        locked_facts_count=locked_facts_count,
    )
