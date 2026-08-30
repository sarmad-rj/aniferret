"""Tests for episode-aware bounty resolution. A character's bounty isn't a fixed stat —
it climbs over the series, so the dossier must show whichever bounty milestone is the
most recent one already unlocked at the user's checkpoint, not always the same value.
"""

from app.schemas.dossier import RevealedFact
from app.services import ingestion_service
from app.services.dossier_service import _current_bounty
from app.services.ingestion_service import ExtractedFact, import_anime
from tests.conftest import TestSessionLocal


def _bounty_fact(fact_id: int, amount: str, first_revealed_at: str) -> RevealedFact:
    return RevealedFact(
        fact_id=fact_id,
        subject="Test",
        predicate="bounty",
        object=amount,
        source_citation="test",
        first_revealed_at=first_revealed_at,
        first_hinted_at=None,
    )


# --- _current_bounty (pure unit tests) ---


def test_current_bounty_falls_back_to_static_value_when_character_has_no_bounty_history() -> None:
    assert _current_bounty("30,000,000", [], has_bounty_history=False) == "30,000,000"


def test_current_bounty_hides_static_value_when_history_exists_but_nothing_unlocked_yet() -> None:
    """Regression: the static value is a character's *current/final* real-world bounty
    (e.g. Luffy's post-timeskip 3,000,000,000 scraped from his bio), so showing it before
    any milestone fact unlocks would leak the endgame amount at Episode 1. Must hide it
    (return None) instead, once we know this character has a tracked history at all.
    """
    assert _current_bounty("3,000,000,000", [], has_bounty_history=True) is None


def test_current_bounty_uses_the_single_bounty_fact_over_the_static_value() -> None:
    facts = [_bounty_fact(1, "30,000,000", "S1E1")]

    assert _current_bounty("100,000,000", facts, has_bounty_history=True) == "30,000,000"


def test_current_bounty_picks_the_latest_of_several_bounty_facts() -> None:
    facts = [
        _bounty_fact(1, "30,000,000", "S1E1"),
        _bounty_fact(2, "100,000,000", "S1E44"),
        _bounty_fact(3, "300,000,000", "S1E95"),
    ]

    assert _current_bounty(None, facts, has_bounty_history=True) == "300,000,000"


def test_current_bounty_is_order_independent() -> None:
    facts = [
        _bounty_fact(3, "300,000,000", "S1E95"),
        _bounty_fact(1, "30,000,000", "S1E1"),
        _bounty_fact(2, "100,000,000", "S1E44"),
    ]

    assert _current_bounty(None, facts, has_bounty_history=True) == "300,000,000"


def test_current_bounty_ignores_non_bounty_facts() -> None:
    facts = [
        RevealedFact(
            fact_id=1,
            subject="Test",
            predicate="devil_fruit_power",
            object="Gomu Gomu no Mi",
            source_citation="test",
            first_revealed_at="S1E1",
            first_hinted_at=None,
        )
    ]

    assert _current_bounty("30,000,000", facts, has_bounty_history=False) == "30,000,000"


# --- end-to-end: the dossier endpoint actually resolves a different bounty per checkpoint ---


async def _fake_resolve_mal_id(query: str) -> int:
    return 313131313


async def _fake_fetch_jikan_metadata(mal_id: int) -> dict:
    return {"title": "Bounty Test Anime", "episodes": 200, "score": 8.0, "synopsis": "..."}


async def _fake_fetch_anilist_metadata(mal_id: int) -> None:
    return None


async def _fake_fetch_character_roster(mal_id: int, limit: int = 8) -> list[dict]:
    return [
        {
            "name": "Test Captain",
            "description": "__Bounty:__ 300,000,000 (previously 30,000,000, 100,000,000)",
            "role": "MAIN",
            "avatar_url": None,
        }
    ]


def _fake_extract_debut_episode(name: str, description: str, max_episode: int) -> str:
    return "S1E1"


def _fake_extract_facts_with_bounty_history(
    name: str, description: str, max_episode: int
) -> list[ExtractedFact]:
    return [
        ExtractedFact(
            subject=name, predicate="bounty", object="30,000,000",
            first_revealed_at="S1E1", first_hinted_at=None, confidence=0.95,
        ),
        ExtractedFact(
            subject=name, predicate="bounty", object="100,000,000",
            first_revealed_at="S1E44", first_hinted_at=None, confidence=0.9,
        ),
        ExtractedFact(
            subject=name, predicate="bounty", object="300,000,000",
            first_revealed_at="S1E95", first_hinted_at=None, confidence=0.9,
        ),
    ]


async def test_dossier_shows_the_bounty_milestone_unlocked_at_each_checkpoint(
    monkeypatch, client
) -> None:
    monkeypatch.setattr(ingestion_service, "resolve_mal_id", _fake_resolve_mal_id)
    monkeypatch.setattr(ingestion_service, "fetch_jikan_metadata", _fake_fetch_jikan_metadata)
    monkeypatch.setattr(ingestion_service, "fetch_anilist_metadata", _fake_fetch_anilist_metadata)
    monkeypatch.setattr(ingestion_service, "fetch_character_roster", _fake_fetch_character_roster)
    monkeypatch.setattr(ingestion_service, "extract_debut_episode", _fake_extract_debut_episode)
    monkeypatch.setattr(
        ingestion_service, "extract_facts_from_character", _fake_extract_facts_with_bounty_history
    )
    monkeypatch.setattr(ingestion_service, "index_facts", lambda pairs: None)

    async with TestSessionLocal() as session:
        anime = await import_anime(session, "Bounty Progression Test")
        slug = anime.slug

    def _bounty_at(episode: int) -> str:
        response = client.get(f"/api/v1/dossier/{slug}", params={"checkpoint": f"S1E{episode}"})
        assert response.status_code == 200
        character = response.json()["characters"][0]
        return character["bounty"]

    assert _bounty_at(1) == "30,000,000"
    assert _bounty_at(43) == "30,000,000"  # still below the next milestone
    assert _bounty_at(44) == "100,000,000"
    assert _bounty_at(94) == "100,000,000"
    assert _bounty_at(95) == "300,000,000"
    assert _bounty_at(200) == "300,000,000"  # stays at the latest unlocked milestone
