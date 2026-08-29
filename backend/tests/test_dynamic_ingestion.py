"""Tests for the autonomous dynamic ingestion pipeline (search/ID -> Gemini fact
extraction -> persist -> vector index). All external HTTP/Gemini calls are mocked so
the suite stays hermetic and fast."""

import pytest
from sqlalchemy import select

from app.models import Character, Faction, TemporalFact
from app.services import ingestion_service
from app.services.ingestion_service import (
    AnimeImportError,
    ExtractedFact,
    _extract_affiliation,
    _is_checkpoint_in_range,
    import_anime,
    resolve_mal_id,
)
from tests.conftest import TestSessionLocal

# --- pure helper functions ---


def test_extract_affiliation_finds_bold_line() -> None:
    description = "__Affiliation:__ Straw Hat Pirates (previously Usopp Pirates)  \nSome text"
    assert _extract_affiliation(description) == "Straw Hat Pirates"


def test_extract_affiliation_strips_spoiler_markers() -> None:
    description = "Affiliation: ~!Secret Group!~ \nmore text"
    assert _extract_affiliation(description) == "Secret Group"


def test_extract_affiliation_returns_none_when_absent() -> None:
    assert _extract_affiliation("Just a plain bio with no structured fields.") is None


def test_is_checkpoint_in_range_accepts_none() -> None:
    assert _is_checkpoint_in_range(None, [24]) is True


def test_is_checkpoint_in_range_accepts_valid() -> None:
    assert _is_checkpoint_in_range("S1E24", [24]) is True


def test_is_checkpoint_in_range_rejects_episode_beyond_season_length() -> None:
    """The exact defensive check that would have caught the One Piece premature-unlock bug."""
    assert _is_checkpoint_in_range("S1E25", [24]) is False


def test_is_checkpoint_in_range_rejects_season_beyond_declared_count() -> None:
    assert _is_checkpoint_in_range("S2E1", [24]) is False


def test_is_checkpoint_in_range_rejects_malformed_checkpoint() -> None:
    assert _is_checkpoint_in_range("not-a-checkpoint", [24]) is False


# --- resolve_mal_id ---


async def test_resolve_mal_id_numeric_query_passthrough() -> None:
    assert await resolve_mal_id("20") == 20


async def test_resolve_mal_id_title_search_success(monkeypatch) -> None:
    class _FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {"data": {"Media": {"idMal": 20}}}

    class _FakeAsyncClient:
        async def __aenter__(self) -> "_FakeAsyncClient":
            return self

        async def __aexit__(self, *args) -> bool:
            return False

        async def post(self, url: str, json: dict | None = None) -> _FakeResponse:
            return _FakeResponse()

    monkeypatch.setattr(ingestion_service.httpx, "AsyncClient", lambda **kwargs: _FakeAsyncClient())

    assert await resolve_mal_id("Naruto") == 20


async def test_resolve_mal_id_returns_none_when_unresolvable(monkeypatch) -> None:
    class _FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {"data": {"Media": None}}

    class _FakeAsyncClient:
        async def __aenter__(self) -> "_FakeAsyncClient":
            return self

        async def __aexit__(self, *args) -> bool:
            return False

        async def post(self, url: str, json: dict | None = None) -> _FakeResponse:
            return _FakeResponse()

    monkeypatch.setattr(ingestion_service.httpx, "AsyncClient", lambda **kwargs: _FakeAsyncClient())

    assert await resolve_mal_id("nonexistent gibberish") is None


# --- extract_facts_from_character ---


def test_extract_facts_returns_empty_without_api_key(monkeypatch) -> None:
    class _FakeSettings:
        gemini_api_key = ""

    monkeypatch.setattr(ingestion_service, "get_settings", lambda: _FakeSettings())

    assert ingestion_service.extract_facts_from_character("Test", "Some bio", 24) == []


def test_extract_facts_returns_empty_for_blank_description(monkeypatch) -> None:
    class _FakeSettings:
        gemini_api_key = "fake-key"

    monkeypatch.setattr(ingestion_service, "get_settings", lambda: _FakeSettings())

    assert ingestion_service.extract_facts_from_character("Test", "   ", 24) == []


# --- import_anime orchestration (external calls mocked) ---


async def _fake_resolve_mal_id(query: str) -> int:
    # Deterministic-per-query so distinct test cases don't collide on mal_id, but the
    # same query always resolves to the same id (needed by the idempotency test).
    return abs(hash(query)) % 900000 + 100000


async def _fake_fetch_jikan_metadata(mal_id: int) -> dict:
    return {"title": "Test Anime", "episodes": 24, "score": 8.0, "synopsis": "A test synopsis."}


async def _fake_fetch_anilist_metadata(mal_id: int) -> None:
    return None


async def _fake_fetch_character_roster(mal_id: int, limit: int = 8) -> list[dict]:
    return [
        {
            "name": "Hero Person",
            "description": "__Affiliation:__ Test Squad\nA brave hero on a quest. ~!Secretly a clone!~",
        },
    ]


def _fake_extract_facts(name: str, description: str, max_episode: int) -> list[ExtractedFact]:
    return [
        ExtractedFact(
            subject=name,
            predicate="true_identity",
            object="Secretly a clone.",
            first_revealed_at="S1E20",
            first_hinted_at="S1E5",
            confidence=0.9,
        ),
        ExtractedFact(
            subject=name,
            predicate="out_of_range_fact",
            object="This checkpoint is invalid on purpose.",
            first_revealed_at="S1E999",  # exceeds max_episode=24 — must be dropped
            first_hinted_at=None,
            confidence=0.8,
        ),
    ]


@pytest.fixture(autouse=True)
def _mock_provider_calls(monkeypatch):
    """Mocks the external metadata/roster/indexing calls for every test in this file.

    Deliberately does NOT touch extract_facts_from_character — the two unit tests below
    test that function directly, so an autouse mock of it here would shadow the very
    thing they're testing. Tests that need extraction mocked opt in via _mock_extraction.
    """
    monkeypatch.setattr(ingestion_service, "resolve_mal_id", _fake_resolve_mal_id)
    monkeypatch.setattr(ingestion_service, "fetch_jikan_metadata", _fake_fetch_jikan_metadata)
    monkeypatch.setattr(ingestion_service, "fetch_anilist_metadata", _fake_fetch_anilist_metadata)
    monkeypatch.setattr(ingestion_service, "fetch_character_roster", _fake_fetch_character_roster)
    monkeypatch.setattr(ingestion_service, "index_facts", lambda pairs: None)


@pytest.fixture
def _mock_extraction(monkeypatch):
    monkeypatch.setattr(ingestion_service, "extract_facts_from_character", _fake_extract_facts)


async def _fake_fetch_character_roster_no_affiliation_line(mal_id: int, limit: int = 8) -> list[dict]:
    return [{"name": "Plain Bio Hero", "description": "A hero with no structured bio fields."}]


def _fake_extract_facts_with_faction_field(
    name: str, description: str, max_episode: int
) -> list[ExtractedFact]:
    return [
        ExtractedFact(
            subject=name,
            predicate="team_membership",
            object="Fights alongside the Justice Squad.",
            first_revealed_at="S1E3",
            first_hinted_at=None,
            confidence=0.85,
            faction="Justice Squad",
        ),
    ]


@pytest.fixture
def _mock_extraction_with_faction_fallback(monkeypatch):
    """Bio has no 'Affiliation:' line — faction must come from Gemini's own faction field."""
    monkeypatch.setattr(
        ingestion_service, "fetch_character_roster", _fake_fetch_character_roster_no_affiliation_line
    )
    monkeypatch.setattr(
        ingestion_service, "extract_facts_from_character", _fake_extract_facts_with_faction_field
    )


async def test_import_anime_creates_anime_with_correct_metadata(_mock_extraction) -> None:
    async with TestSessionLocal() as session:
        anime = await import_anime(session, "Test Anime")

        assert anime.slug == "test-anime"
        assert anime.title == "Test Anime"
        assert anime.total_episodes == 24
        assert anime.season_episode_counts == [24]


async def test_import_anime_creates_faction_from_affiliation() -> None:
    async with TestSessionLocal() as session:
        anime = await import_anime(session, "Test Anime 2")

        faction_result = await session.execute(select(Faction).where(Faction.anime_id == anime.id))
        factions = faction_result.scalars().all()
        assert any(faction.name == "Test Squad" for faction in factions)

        character_result = await session.execute(
            select(Character).where(Character.anime_id == anime.id)
        )
        character = character_result.scalars().one()
        assert character.faction_id is not None


async def test_import_anime_falls_back_to_gemini_faction_when_no_affiliation_line(
    _mock_extraction_with_faction_fallback,
) -> None:
    async with TestSessionLocal() as session:
        anime = await import_anime(session, "Test Anime 7")

        faction_result = await session.execute(select(Faction).where(Faction.anime_id == anime.id))
        factions = faction_result.scalars().all()
        assert any(faction.name == "Justice Squad" for faction in factions)


async def test_import_anime_drops_out_of_range_checkpoint_facts(_mock_extraction) -> None:
    async with TestSessionLocal() as session:
        anime = await import_anime(session, "Test Anime 3")

        fact_result = await session.execute(
            select(TemporalFact).where(TemporalFact.anime_id == anime.id)
        )
        facts = fact_result.scalars().all()

        assert len(facts) == 1  # only the in-range fact should survive validation
        assert facts[0].predicate == "true_identity"
        assert facts[0].first_revealed_at == "S1E20"
        assert facts[0].source == "gemini_extracted"


async def test_import_anime_is_idempotent_by_mal_id() -> None:
    async with TestSessionLocal() as session:
        first = await import_anime(session, "Test Anime 4")
        second = await import_anime(session, "Test Anime 4")

        assert first.id == second.id


async def test_import_anime_raises_when_unresolvable(monkeypatch) -> None:
    async def _unresolvable(query: str) -> None:
        return None

    monkeypatch.setattr(ingestion_service, "resolve_mal_id", _unresolvable)

    async with TestSessionLocal() as session:
        with pytest.raises(AnimeImportError):
            await import_anime(session, "nonexistent")


async def test_import_anime_raises_when_no_metadata_available(monkeypatch) -> None:
    async def _no_metadata(mal_id: int) -> None:
        return None

    monkeypatch.setattr(ingestion_service, "fetch_jikan_metadata", _no_metadata)
    monkeypatch.setattr(ingestion_service, "fetch_anilist_metadata", _no_metadata)

    async with TestSessionLocal() as session:
        with pytest.raises(AnimeImportError):
            await import_anime(session, "Test Anime 5")


# --- rich dossier metadata + faction/crew hierarchy classification ---


async def _fake_fetch_character_roster_rich(mal_id: int, limit: int = 8) -> list[dict]:
    return [
        {
            "name": "Test Captain",
            "description": (
                "__Height:__ 172 cm\n"
                "__Affiliation:__ Straw Hat Pirates (current)\n"
                "__Bounty:__ 3,000,000,000\n"
                "__Devil Fruit:__ Gomu Gomu no Mi\n"
                "A carefree captain chasing a dream. ~!Secretly royalty!~"
            ),
            "role": "MAIN",
            "avatar_url": "https://anilist.example/captain.jpg",
        }
    ]


def _fake_extract_facts_rich(name: str, description: str, max_episode: int) -> list[ExtractedFact]:
    return [
        ExtractedFact(
            subject=name,
            predicate="hidden_lineage",
            object="Secretly royalty.",
            first_revealed_at="S1E15",
            first_hinted_at="S1E5",
            confidence=0.9,
        ),
    ]


@pytest.fixture
def _mock_rich_roster(monkeypatch):
    monkeypatch.setattr(
        ingestion_service, "fetch_character_roster", _fake_fetch_character_roster_rich
    )
    monkeypatch.setattr(ingestion_service, "extract_facts_from_character", _fake_extract_facts_rich)


async def test_import_anime_captures_rich_character_metadata(_mock_rich_roster) -> None:
    async with TestSessionLocal() as session:
        anime = await import_anime(session, "Test Anime 8")

        character_result = await session.execute(
            select(Character).where(Character.anime_id == anime.id)
        )
        character = character_result.scalars().one()

        assert character.role == "MAIN"
        assert character.avatar_url == "https://anilist.example/captain.jpg"
        assert character.height == "172 cm"
        assert character.bounty == "3,000,000,000"
        assert character.power == "Gomu Gomu no Mi"
        assert character.backstory is not None and "Secretly royalty" in character.backstory


async def test_import_anime_derives_first_revealed_at_from_earliest_extracted_fact(
    _mock_rich_roster,
) -> None:
    async with TestSessionLocal() as session:
        anime = await import_anime(session, "Test Anime 9")

        character_result = await session.execute(
            select(Character).where(Character.anime_id == anime.id)
        )
        character = character_result.scalars().one()

        assert character.first_revealed_at == "S1E15"


async def test_import_anime_defaults_first_revealed_at_when_no_facts_extracted() -> None:
    async with TestSessionLocal() as session:
        anime = await import_anime(session, "Test Anime 10")

        character_result = await session.execute(
            select(Character).where(Character.anime_id == anime.id)
        )
        character = character_result.scalars().one()

        assert character.first_revealed_at == "S1E1"


async def test_import_anime_nests_pirate_crew_under_pirate_crews_faction(
    _mock_rich_roster,
) -> None:
    async with TestSessionLocal() as session:
        anime = await import_anime(session, "Test Anime 11")

        faction_result = await session.execute(select(Faction).where(Faction.anime_id == anime.id))
        factions = {faction.name: faction for faction in faction_result.scalars().all()}

        assert "Pirate Crews" in factions
        assert "Straw Hat Pirates" in factions
        assert factions["Pirate Crews"].parent_id is None
        assert factions["Straw Hat Pirates"].parent_id == factions["Pirate Crews"].id


# --- endpoint ---


def test_import_anime_endpoint_returns_201(client) -> None:
    response = client.post("/api/v1/anime/import", json={"query": "Test Anime 6"})

    assert response.status_code == 201
    assert response.json()["title"] == "Test Anime"


def test_import_anime_endpoint_returns_404_when_unresolvable(client, monkeypatch) -> None:
    async def _unresolvable(query: str) -> None:
        return None

    monkeypatch.setattr(ingestion_service, "resolve_mal_id", _unresolvable)

    response = client.post("/api/v1/anime/import", json={"query": "nonexistent"})

    assert response.status_code == 404


def test_import_anime_endpoint_rejects_empty_query(client) -> None:
    response = client.post("/api/v1/anime/import", json={"query": ""})

    assert response.status_code == 422
