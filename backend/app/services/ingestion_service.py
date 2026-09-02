"""External metadata ingestion from Jikan REST v4 and AniList GraphQL (SPEC.md D6), plus
the autonomous dynamic ingestion pipeline (search/ID -> metadata + roster -> Gemini fact
extraction -> persistence -> vector indexing).

The D6 ingestion (fetch_jikan_metadata/fetch_anilist_metadata/ingest_anime_sources) is a
deliberate, on-demand operation (run via app/db/ingest_sources.py), never triggered on the
request path — external providers are slow/rate-limited/occasionally unavailable, and a
dossier read must never depend on their uptime. The dynamic import pipeline (import_anime)
*is* request-triggered (POST /api/v1/anime/import) since that's the whole point of it, but
it degrades gracefully at every external step rather than failing the whole import.

Both providers are queried by MAL id: Jikan's own search endpoint is flaky upstream, but
its by-id lookup is reliable, and AniList's schema accepts an `idMal` argument directly —
so a single MAL id is enough to look up both, without needing AniList's separate ID space.
Title search also goes through AniList (its `search` argument is reliable) rather than
Jikan's search endpoint, for the same reason.
"""

import logging
import re

import httpx
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.anime import Anime
from app.models.anime_external_metadata import AnimeExternalMetadata
from app.models.character import Character
from app.models.faction import Faction
from app.models.temporal_fact import TemporalFact
from app.services.faction_classifier import classify_affiliation
from app.services.reveal_engine import InvalidCheckpointError, parse_checkpoint
from app.services.vector_store import index_facts

logger = logging.getLogger(__name__)

_TIMEOUT = 15.0
_ANILIST_URL = "https://graphql.anilist.co"
_ANILIST_QUERY = """
query ($idMal: Int) {
  Media(idMal: $idMal, type: ANIME) {
    title { romaji }
    episodes
    averageScore
    description(asHtml: false)
    coverImage { large }
    genres
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
        "cover_image_url": ((data.get("images") or {}).get("jpg") or {}).get("large_image_url"),
        "genres": [genre["name"] for genre in data.get("genres") or [] if genre.get("name")],
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
        "cover_image_url": (media.get("coverImage") or {}).get("large"),
        "genres": media.get("genres") or [],
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


# ---------------------------------------------------------------------------
# Autonomous dynamic ingestion: search/ID -> metadata + roster -> Gemini fact
# extraction -> persistence -> vector indexing.
# ---------------------------------------------------------------------------


class AnimeImportError(Exception):
    """Raised when an anime cannot be resolved, or has no usable metadata from either provider."""


class ExtractedFact(BaseModel):
    """Gemini's structured-output shape for one atomic fact extracted from a character bio."""

    subject: str
    predicate: str
    object: str
    first_revealed_at: str
    first_hinted_at: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    faction: str | None = Field(
        default=None,
        description="A named group/team/organization the subject belongs to, if evident; else null.",
    )


_ANILIST_SEARCH_QUERY = """
query ($search: String) {
  Media(search: $search, type: ANIME) {
    idMal
  }
}
"""

_ANILIST_CHARACTERS_QUERY = """
query ($idMal: Int, $perPage: Int) {
  Media(idMal: $idMal, type: ANIME) {
    characters(sort: ROLE, perPage: $perPage) {
      edges {
        role
        node {
          name { full first middle last }
          description(asHtml: false)
          image { large }
        }
      }
    }
  }
}
"""

_DEFAULT_EPISODE_FALLBACK = 24
"""Used only when neither provider reports an episode count (e.g. an ongoing/RELEASING
series like One Piece, where the real total isn't fixed) — a conservative single-season
default rather than guessing an arbitrarily large number."""

_MAX_CHARACTERS_TO_INGEST = 40
"""Was 8 — a deliberately small demo-safe default from when this pipeline was new and
unproven. Each character costs 2 Gemini calls (extract_facts_from_character +
extract_debut_episode; see below), so this is the real lever on both API spend and
free-tier request-per-day usage, independent of Gemini's own account-level rate limit.
Changing this number alone makes zero Gemini calls by itself — it only takes effect the
next time import_anime/ingest_character_roster actually runs."""

_EXTRACTION_MODEL_NAME = "gemini-3.6-flash"

_AFFILIATION_RE = re.compile(r"Affiliations?:[*_]*\s*([^\n\r(]+)", re.IGNORECASE)
"""Matches AniList's markdown convention, e.g. '__Affiliation:__ Straw Hat Pirates (...)' or
the plural '__Affiliations:__ ...' variant some bios use (e.g. Luffy's) — [*_]* eats the
closing bold marker, whether it's asterisks or (AniList's actual style) underscores."""

_BOUNTY_RE = re.compile(r"Bount(?:y|ies):[*_]*\s*([^\n\r(]+)", re.IGNORECASE)
_POWER_RE = re.compile(r"(?:Devil Fruit|Power|Ability|Haki):[*_]*\s*([^\n\r(]+)", re.IGNORECASE)
_HEIGHT_RE = re.compile(r"Height:[*_]*\s*([^\n\r(]+)", re.IGNORECASE)
"""Same structured-bio-line convention as Affiliation: — used to dynamically capture rich
dossier metadata (bounty, power, height) straight from AniList bio text rather than
hardcoding it per character."""

_EXTRACTION_SYSTEM_INSTRUCTION = (
    "You are AniFerret's fact extraction engine. Given a character's public bio/wiki "
    "description, extract 1 to 3 atomic, spoiler-relevant facts about them as structured "
    "JSON. Each fact needs: subject (the character's name, exactly as given), predicate "
    "(a short snake_case relation, e.g. 'true_identity', 'special_ability', "
    "'family_relation'), object (the revealed content, one sentence, no spoiler markup), "
    "first_revealed_at (a plausible checkpoint 'S1E<n>' with n between 1 and {max_episode} "
    "inclusive), first_hinted_at (an earlier checkpoint if the fact is foreshadowed before "
    "its full reveal, else null), confidence (0.0-1.0: your certainty this is accurate and "
    "genuinely spoiler-relevant, not trivia), and faction (the name of a team, squad, "
    "crew, division, guild, or organization the character clearly belongs to, if the bio "
    "states one — else null; do not guess or infer one that isn't explicitly stated).\n\n"
    "If the bio's Bounty line lists a history of prior values (e.g. 'X (previously Y, "
    "Z)'), extract each distinct bounty value as its own fact with predicate 'bounty' and "
    "object set to just the numeric amount (no commentary) — first_revealed_at should be "
    "the checkpoint at which that amount became their bounty, increasing over the series "
    "(earlier amounts get earlier checkpoints, the current amount the latest/highest "
    "checkpoint you can justify). Skip this if the bio gives no such history.\n\n"
    "The bio text may contain spoiler markers: content between ~! and !~ is community-"
    "flagged as a spoiler by the source. Facts drawn from inside those markers must get a "
    "first_revealed_at well into the series (a high episode number, not episode 1) — "
    "reflecting that they're revealed late. Facts drawn from outside those markers (plain "
    "introductory bio info) should get an early first_revealed_at. Never invent facts the "
    "text doesn't support, and never output a fact with no textual basis."
)


async def resolve_mal_id(query: str) -> int | None:
    """Resolve a free-text title or a numeric-string MAL id into a MAL id.

    A purely numeric query is treated as an existing MAL id directly. Otherwise, title
    search goes through AniList's `search` argument — Jikan's own search endpoint 504s
    unreliably upstream, but AniList's is stable and returns `idMal` directly.
    """
    stripped = query.strip()
    if stripped.isdigit():
        return int(stripped)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                _ANILIST_URL,
                json={"query": _ANILIST_SEARCH_QUERY, "variables": {"search": stripped}},
            )
            response.raise_for_status()
    except httpx.HTTPError:
        return None

    media = (response.json().get("data") or {}).get("Media")
    return media.get("idMal") if media else None


def _format_display_name(name_node: dict) -> str:
    """Reorder AniList's structured name into the family-name-first convention these
    titles are commonly known by, dynamically, per character.

    AniList's `full` field is always given-name-first (Western order) even for
    Japanese-origin characters — e.g. for Luffy it reports first='Luffy', middle='D.',
    last='Monkey', full='Luffy Monkey' — so displaying `full` verbatim produces reversed
    names like 'Luffy Monkey' or 'Zoro Roronoa' instead of 'Monkey D. Luffy' / 'Roronoa
    Zoro'. Rebuilding as last + middle + first (falling back to `first`/`full` when no
    last name is on file, e.g. 'Nami') fixes this from AniList's own structured fields —
    no per-character name table involved.
    """
    first = (name_node.get("first") or "").strip()
    middle = (name_node.get("middle") or "").strip()
    last = (name_node.get("last") or "").strip()
    if last:
        return " ".join(part for part in (last, middle, first) if part)
    return first or (name_node.get("full") or "").strip()


async def fetch_character_roster(mal_id: int, limit: int = _MAX_CHARACTERS_TO_INGEST) -> list[dict]:
    """Fetch up to `limit` characters (main cast first) with their bio text, via AniList.

    AniList's character bios consistently include an 'Affiliation:' line (used to derive
    factions) and wrap spoiler-sensitive content in ~!...!~ markers (used to steer Gemini's
    checkpoint placement) — both are why this goes through AniList rather than Jikan, which
    offers neither on its anime-characters endpoint.
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                _ANILIST_URL,
                json={
                    "query": _ANILIST_CHARACTERS_QUERY,
                    "variables": {"idMal": mal_id, "perPage": limit},
                },
            )
            response.raise_for_status()
    except httpx.HTTPError:
        return []

    media = (response.json().get("data") or {}).get("Media")
    if not media:
        return []

    edges = (media.get("characters") or {}).get("edges") or []
    roster = []
    for edge in edges:
        node = edge.get("node") or {}
        name = _format_display_name(node.get("name") or {})
        if name:
            roster.append(
                {
                    "name": name,
                    "description": node.get("description") or "",
                    "role": edge.get("role"),
                    "avatar_url": (node.get("image") or {}).get("large"),
                }
            )
    return roster


def _extract_bio_field(description: str, pattern: re.Pattern[str]) -> str | None:
    """Pull one structured 'Label: value' line out of an AniList bio, dynamically.

    Used for Affiliation, Bounty, Power/Devil Fruit, and Height — all follow the same
    community-authored markdown convention, so a single helper covers all of them
    without any per-character hardcoding.
    """
    match = pattern.search(description)
    if not match:
        return None
    cleaned = match.group(1).replace("~!", "").replace("!~", "").strip().strip("*").strip()
    return cleaned or None


def _extract_affiliation(description: str) -> str | None:
    """Pull a character's group/organization from AniList's 'Affiliation:' bio convention."""
    return _extract_bio_field(description, _AFFILIATION_RE)


_STRUCTURED_BIO_LINE_RE = re.compile(r"^[*_]{2}[^*_\n:]+:[*_]{2}.*$", re.MULTILINE)
"""Matches a whole AniList structured bio line, e.g. '__Height:__ 174 cm' or
'__Bounty:__ 500,000,000 (...)' — covers every such line generically (Height,
Affiliation, Bounty, Devil Fruit, Position, etc.), not just the specific fields parsed
into their own dossier columns above."""


def _clean_backstory(description: str) -> str | None:
    """Strip AniList's structured '__Label:__ value' header lines out of a bio, leaving
    only the prose narrative — those fields are already surfaced as their own dossier
    stats (height/bounty/power/affiliation), so repeating them inside the backstory text
    is redundant clutter rather than a spoiler concern.
    """
    spoiler_markers_removed = description.replace("~!", "").replace("!~", "")
    without_headers = _STRUCTURED_BIO_LINE_RE.sub("", spoiler_markers_removed)
    paragraphs = [line.strip() for line in without_headers.split("\n") if line.strip()]
    return "\n\n".join(paragraphs) or None


def _is_checkpoint_in_range(checkpoint: str | None, season_episode_counts: list[int]) -> bool:
    """Validate a checkpoint actually fits within the anime's declared season lengths.

    This is the exact defensive check that would have caught the One Piece premature-
    unlock bug: is_revealed() compares (season, episode) tuples with no notion of season
    length, so an LLM-generated checkpoint that overshoots its season's real length could
    let a later-season checkpoint prematurely satisfy it. Since this pipeline has no human
    reviewing Gemini's output before it reaches the DB, checkpoints must be validated here.
    """
    if checkpoint is None:
        return True
    try:
        season, episode = parse_checkpoint(checkpoint)
    except InvalidCheckpointError:
        return False
    return 1 <= season <= len(season_episode_counts) and 1 <= episode <= season_episode_counts[season - 1]


def extract_facts_from_character(
    character_name: str, description: str, max_episode: int
) -> list[ExtractedFact]:
    """Ask Gemini to extract atomic Temporal Facts from one character's bio text.

    Returns an empty list on a missing API key, empty description, or any failure (network,
    quota, malformed response) — ingestion must degrade to "no facts extracted", never fail
    the whole import over one character's extraction call.
    """
    settings = get_settings()
    if not settings.gemini_api_key or not description.strip():
        return []

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=_EXTRACTION_MODEL_NAME,
            contents=f"Character: {character_name}\n\nBio:\n{description[:4000]}",
            config=types.GenerateContentConfig(
                system_instruction=_EXTRACTION_SYSTEM_INSTRUCTION.format(max_episode=max_episode),
                response_mime_type="application/json",
                response_schema=list[ExtractedFact],
            ),
        )
        raw_facts = response.parsed or []
    except Exception:
        logger.warning("Gemini fact extraction failed for %r", character_name, exc_info=True)
        return []

    validated: list[ExtractedFact] = []
    for raw in raw_facts:
        try:
            validated.append(raw if isinstance(raw, ExtractedFact) else ExtractedFact.model_validate(raw))
        except ValidationError:
            continue
    return validated


# ---------------------------------------------------------------------------
# Dynamic canon debut extraction: a character's first appearance / crew-join
# episode, determined by the LLM from its own knowledge + bio text. There is no
# hardcoded episode map and no fallback to episode 1 — an undetermined debut means
# the character is skipped entirely (see _ingest_character), never silently shown.
# ---------------------------------------------------------------------------


class DebutInfo(BaseModel):
    """Gemini's structured-output shape for one character's canon debut timing."""

    debut_episode: int | None = Field(
        default=None,
        description=(
            "The episode number (1-indexed) of this character's canonical first "
            "appearance in the anime. Null if genuinely not determinable with "
            "reasonable confidence — never guess."
        ),
    )
    crew_join_episode: int | None = Field(
        default=None,
        description=(
            "The episode number this character officially joins their stated crew/"
            "faction, only if that's known and later than their debut; else null."
        ),
    )


_DEBUT_EXTRACTION_SYSTEM_INSTRUCTION = (
    "You are AniFerret's canon debut extraction engine. Given a character's name and "
    "public bio/wiki description from an anime with {max_episode} total episodes, use "
    "your own knowledge of the source material together with the bio text to determine: "
    "debut_episode (the episode number of this character's canonical first on-screen "
    "appearance) and crew_join_episode (the episode they officially join their stated "
    "crew/faction, only if that is known and later than their debut). Both must be "
    "integers between 1 and {max_episode} inclusive when known. If you cannot determine "
    "the debut episode with reasonable confidence, return null for debut_episode — never "
    "default to episode 1 and never guess."
)


def _resolve_debut_checkpoint(
    debut_episode: int | None, crew_join_episode: int | None, max_episode: int
) -> str | None:
    """Combine debut + crew-join episodes into the single checkpoint at which a
    character is safe to show as an introduced member of their faction: the later of
    the two, restricted to in-range values. None (unknown/undeterminable) if neither
    candidate is a valid in-range episode number.
    """
    candidates = [
        episode
        for episode in (debut_episode, crew_join_episode)
        if episode is not None and 1 <= episode <= max_episode
    ]
    if not candidates:
        return None
    return f"S1E{max(candidates)}"


def extract_debut_episode(character_name: str, description: str, max_episode: int) -> str | None:
    """Ask Gemini for a character's canon debut checkpoint via the LLM extraction
    pipeline — the sole source of truth for when a character is introduced.

    Returns None on a missing API key, any failure (network, quota, malformed
    response), or when the model itself reports no confident debut episode. Callers
    must treat None as "exclude this character entirely", never default to episode 1.
    """
    settings = get_settings()
    if not settings.gemini_api_key or not description.strip():
        return None

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=_EXTRACTION_MODEL_NAME,
            contents=f"Character: {character_name}\n\nBio:\n{description[:4000]}",
            config=types.GenerateContentConfig(
                system_instruction=_DEBUT_EXTRACTION_SYSTEM_INSTRUCTION.format(max_episode=max_episode),
                response_mime_type="application/json",
                response_schema=DebutInfo,
            ),
        )
        parsed = response.parsed
    except Exception:
        logger.warning("Gemini debut extraction failed for %r", character_name, exc_info=True)
        return None

    if parsed is None:
        return None
    try:
        info = parsed if isinstance(parsed, DebutInfo) else DebutInfo.model_validate(parsed)
    except ValidationError:
        return None

    return _resolve_debut_checkpoint(info.debut_episode, info.crew_join_episode, max_episode)


async def _generate_unique_slug(session: AsyncSession, title: str, mal_id: int) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or f"anime-{mal_id}"
    candidate = base
    suffix = 2
    while True:
        existing = await session.execute(select(Anime).where(Anime.slug == candidate))
        if existing.scalar_one_or_none() is None:
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1


_FactionCache = dict[tuple[int | None, str], Faction]
"""Keyed by (parent_faction_id, name) so a top-level faction and a same-named crew never
collide, and so repeated affiliations within one roster reuse the same row."""


async def _get_or_create_faction(
    session: AsyncSession, anime_id: int, name: str, parent_id: int | None, cache: _FactionCache
) -> Faction:
    key = (parent_id, name)
    cached = cache.get(key)
    if cached is not None:
        return cached

    faction = Faction(anime_id=anime_id, name=name, parent_id=parent_id)
    session.add(faction)
    await session.flush()
    cache[key] = faction
    return faction


async def _resolve_faction(
    session: AsyncSession, anime_id: int, affiliation: str, cache: _FactionCache
) -> Faction:
    """Resolve a free-text affiliation into a persisted Faction, nesting it under the
    matching top-level Faction/Crew hierarchy (see faction_classifier) when recognized,
    or as a flat, standalone faction named after the affiliation otherwise.
    """
    top_level_name, crew_name = classify_affiliation(affiliation)
    if top_level_name is None:
        return await _get_or_create_faction(session, anime_id, affiliation, None, cache)

    top_level = await _get_or_create_faction(session, anime_id, top_level_name, None, cache)
    if crew_name is None:
        return top_level
    return await _get_or_create_faction(session, anime_id, crew_name, top_level.id, cache)


async def _ingest_character(
    session: AsyncSession,
    anime: Anime,
    character_data: dict,
    max_episode: int,
    season_episode_counts: list[int],
    faction_cache: _FactionCache,
) -> tuple[Character, list[tuple[TemporalFact, str]]] | None:
    """Extract facts + rich dossier metadata for one roster entry, persist the Character
    (with faction/crew classification and a dynamically extracted canon debut
    checkpoint), and return it alongside the (fact, anime_slug) pairs still pending
    vector indexing.

    Returns None — the caller must skip this character entirely — when
    extract_debut_episode can't determine a confident canon debut checkpoint. There is
    no hardcoded episode map and no fallback to episode 1: an unknown debut means the
    character never enters Factions or the UI roster, at any checkpoint.
    """
    name = character_data["name"]
    description = character_data["description"]

    first_revealed_at = extract_debut_episode(name, description, max_episode)
    if first_revealed_at is None:
        logger.info(
            "Skipping %r: no confidently-determined canon debut episode from the "
            "dynamic extraction pipeline (never defaulting to episode 1).",
            name,
        )
        return None

    extracted_facts = extract_facts_from_character(name, description, max_episode)

    # The 'Affiliation:' bio convention isn't universal (One Piece's bios use it,
    # Naruto's/Bleach's don't) — fall back to whatever Gemini itself identified from
    # the full bio text when the regex heuristic finds nothing.
    affiliation = _extract_affiliation(description) or next(
        (fact.faction for fact in extracted_facts if fact.faction), None
    )
    faction = (
        await _resolve_faction(session, anime.id, affiliation, faction_cache) if affiliation else None
    )

    valid_facts: list[ExtractedFact] = []
    for fact_data in extracted_facts:
        if not _is_checkpoint_in_range(fact_data.first_revealed_at, season_episode_counts):
            logger.warning(
                "Dropping extracted fact with out-of-range first_revealed_at=%s for %r",
                fact_data.first_revealed_at,
                name,
            )
            continue
        if not _is_checkpoint_in_range(fact_data.first_hinted_at, season_episode_counts):
            fact_data.first_hinted_at = None  # optional field — drop just the hint, not the fact
        valid_facts.append(fact_data)

    character = Character(
        anime_id=anime.id,
        name=name,
        faction_id=faction.id if faction else None,
        role=character_data.get("role"),
        avatar_url=character_data.get("avatar_url"),
        height=_extract_bio_field(description, _HEIGHT_RE),
        bounty=_extract_bio_field(description, _BOUNTY_RE),
        power=_extract_bio_field(description, _POWER_RE),
        backstory=_clean_backstory(description),
        first_revealed_at=first_revealed_at,
    )
    session.add(character)

    indexed_pairs: list[tuple[TemporalFact, str]] = []
    for fact_data in valid_facts:
        fact = TemporalFact(
            anime_id=anime.id,
            subject=fact_data.subject,
            predicate=fact_data.predicate,
            object=fact_data.object,
            source_citation=f"AniList character bio — {name}",
            first_revealed_at=fact_data.first_revealed_at,
            first_hinted_at=fact_data.first_hinted_at,
            confidence=fact_data.confidence,
            source="gemini_extracted",
        )
        session.add(fact)
        indexed_pairs.append((fact, anime.slug))

    return character, indexed_pairs


async def ingest_character_roster(
    session: AsyncSession, anime: Anime, roster: list[dict]
) -> list[tuple[TemporalFact, str]]:
    """Persist a fetched character roster onto an already-created Anime: fact extraction,
    dossier metadata, faction/crew classification, all in one pass. Commits and vector-
    indexes the result. Returns the (fact, anime_slug) pairs that were indexed.

    Shared by import_anime (full dynamic import) and app/db/seed.py (dynamic roster
    seeding for launch-corpus anime that shouldn't ship with a hardcoded character list).
    """
    season_episode_counts = anime.season_episode_counts or [anime.total_episodes]
    faction_cache: _FactionCache = {}
    indexed_pairs: list[tuple[TemporalFact, str]] = []

    for character_data in roster:
        result = await _ingest_character(
            session, anime, character_data, anime.total_episodes, season_episode_counts, faction_cache
        )
        if result is None:
            continue
        _character, fact_pairs = result
        indexed_pairs.extend(fact_pairs)

    await session.commit()
    for fact, _slug in indexed_pairs:
        await session.refresh(fact)

    try:
        index_facts(indexed_pairs)
    except Exception:
        logger.warning(
            "Vector indexing failed for anime %r; facts remain gated via SQL.",
            anime.slug,
            exc_info=True,
        )

    return indexed_pairs


async def import_anime(session: AsyncSession, query: str) -> Anime:
    """End-to-end dynamic ingestion: resolve -> metadata + roster -> Gemini facts -> persist -> index.

    Idempotent by mal_id: if a matching anime already exists, it's returned as-is rather
    than re-ingested, so repeated imports of the same title don't create duplicate data.
    """
    mal_id = await resolve_mal_id(query)
    if mal_id is None:
        raise AnimeImportError(f"Could not resolve an anime for {query!r} via Jikan or AniList.")

    existing = await session.execute(select(Anime).where(Anime.mal_id == mal_id))
    existing_anime = existing.scalar_one_or_none()
    if existing_anime is not None:
        return existing_anime

    jikan_data = await fetch_jikan_metadata(mal_id)
    anilist_data = await fetch_anilist_metadata(mal_id)
    metadata = jikan_data or anilist_data
    if metadata is None:
        raise AnimeImportError(f"No metadata available for MAL id {mal_id} from either provider.")

    title = metadata.get("title") or query.strip()
    episodes = (jikan_data or {}).get("episodes") or (anilist_data or {}).get("episodes")
    episodes = episodes or _DEFAULT_EPISODE_FALLBACK
    season_episode_counts = [episodes]
    slug = await _generate_unique_slug(session, title, mal_id)

    anime = Anime(
        slug=slug,
        title=title,
        total_episodes=episodes,
        season_episode_counts=season_episode_counts,
        mal_id=mal_id,
        anilist_id=mal_id,
        cover_image_url=(jikan_data or {}).get("cover_image_url")
        or (anilist_data or {}).get("cover_image_url"),
        genres=(jikan_data or {}).get("genres") or (anilist_data or {}).get("genres") or [],
        synopsis=metadata.get("synopsis"),
        score=(jikan_data or {}).get("score") or (anilist_data or {}).get("score"),
    )
    session.add(anime)
    await session.flush()

    roster = await fetch_character_roster(mal_id)
    await ingest_character_roster(session, anime, roster)

    await session.refresh(anime)
    return anime
