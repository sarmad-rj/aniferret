"""Automated verification of the Dynamic Canon Debut Extraction engine
(app/services/ingestion_service.py: extract_debut_episode, _ingest_character) across a
realistic, One-Piece-shaped synthetic roster.

All external calls (metadata, roster fetch, LLM debut/fact extraction) are mocked with
deterministic, hand-picked canon debut episodes so the suite is hermetic and fast, while
still exercising the real ingestion -> dossier_service -> API pipeline end to end. This
is a *test-time* stand-in for the LLM boundary only — the production code path
(extract_debut_episode) always calls Gemini and never hardcodes an episode map or
defaults to episode 1; that contract is what test_dynamic_ingestion.py's
test_import_anime_skips_character_with_unknown_debut_episode etc. verify directly.
"""

from fastapi.testclient import TestClient

from app.services import ingestion_service
from app.services.ingestion_service import import_anime
from tests.conftest import TestSessionLocal

_TOTAL_EPISODES = 1120
_MAL_ID = 20250829  # deliberately outside test_dynamic_ingestion.py's hashed mal_id range

# name -> (canon debut episode, or None if genuinely undeterminable; affiliation)
_ROSTER_DEBUTS: dict[str, tuple[int | None, str]] = {
    "Monkey D. Luffy": (1, "Straw Hat Pirates"),  # protagonist / pilot episode
    "Roronoa Zoro": (3, "Straw Hat Pirates"),  # early ally, introduced by ep. 3
    "Nami": (8, "Straw Hat Pirates"),  # early saga crew
    "Usopp": (9, "Straw Hat Pirates"),  # early saga crew
    "Sanji": (20, "Straw Hat Pirates"),  # early saga crew
    "Tony Tony Chopper": (83, "Straw Hat Pirates"),  # Grand Line addition
    "Nico Robin": (91, "Straw Hat Pirates"),  # Grand Line addition
    "Franky": (205, "Straw Hat Pirates"),  # cyborg, mid-series addition
    "Brook": (337, "Straw Hat Pirates"),  # musician, late-series addition
    "Jinbe": (432, "Straw Hat Pirates"),  # late-arc ally
    "Bon Clay": (400, "Impel Down Escapees"),  # Impel Down arc character
    "Rebecca": (700, "Dressrosa Gladiators"),  # Dressrosa arc character
    "Smoker": (138, "Marines"),  # first-and-only Marine in this roster
    "Ghost Extra": (None, "Straw Hat Pirates"),  # unknown debut -> must never appear
}

_MID_LATE_SERIES_NAMES = {"Franky", "Brook", "Jinbe"}  # cyborg / musician / late ally
_DRESSROSA_IMPEL_DOWN_NAMES = {"Bon Clay", "Rebecca"}


async def _fake_resolve_mal_id(query: str) -> int:
    return _MAL_ID


async def _fake_fetch_jikan_metadata(mal_id: int) -> dict:
    return {"title": "One Piece", "episodes": _TOTAL_EPISODES, "score": 8.7, "synopsis": "..."}


async def _fake_fetch_anilist_metadata(mal_id: int) -> None:
    return None


async def _fake_fetch_character_roster(mal_id: int, limit: int = 40) -> list[dict]:
    return [
        {
            "name": name,
            "description": f"__Affiliation:__ {affiliation}\nA synthetic test bio for {name}.",
            "role": "MAIN",
            "avatar_url": None,
        }
        for name, (_debut, affiliation) in _ROSTER_DEBUTS.items()
    ]


def _fake_extract_debut_episode(name: str, description: str, max_episode: int) -> str | None:
    debut, _affiliation = _ROSTER_DEBUTS[name]
    return f"S1E{debut}" if debut is not None else None


def _fake_extract_facts_from_character(name: str, description: str, max_episode: int) -> list:
    return []


def _visible_names(client: TestClient, slug: str, episode: int) -> set[str]:
    response = client.get(f"/api/v1/dossier/{slug}", params={"checkpoint": f"S1E{episode}"})
    assert response.status_code == 200
    return {character["name"] for character in response.json()["characters"]}


def _dossier_body(client: TestClient, slug: str, episode: int) -> dict:
    response = client.get(f"/api/v1/dossier/{slug}", params={"checkpoint": f"S1E{episode}"})
    assert response.status_code == 200
    return response.json()


def _faction_names(client: TestClient, slug: str, episode: int) -> set[str]:
    return {faction["name"] for faction in _dossier_body(client, slug, episode)["factions"]}


async def _seed_one_piece_slug(monkeypatch) -> str:
    monkeypatch.setattr(ingestion_service, "resolve_mal_id", _fake_resolve_mal_id)
    monkeypatch.setattr(ingestion_service, "fetch_jikan_metadata", _fake_fetch_jikan_metadata)
    monkeypatch.setattr(ingestion_service, "fetch_anilist_metadata", _fake_fetch_anilist_metadata)
    monkeypatch.setattr(ingestion_service, "fetch_character_roster", _fake_fetch_character_roster)
    monkeypatch.setattr(ingestion_service, "extract_debut_episode", _fake_extract_debut_episode)
    monkeypatch.setattr(
        ingestion_service, "extract_facts_from_character", _fake_extract_facts_from_character
    )
    monkeypatch.setattr(ingestion_service, "index_facts", lambda pairs: None)

    async with TestSessionLocal() as session:
        anime = await import_anime(session, "One Piece Canon Debut Gating Test")
        return anime.slug


# --- Checkpoint Episode 1 ---


async def test_checkpoint_episode_1_shows_only_the_pilot_protagonist(monkeypatch, client) -> None:
    slug = await _seed_one_piece_slug(monkeypatch)

    names = _visible_names(client, slug, 1)

    assert names == {"Monkey D. Luffy"}


async def test_checkpoint_episode_1_excludes_mid_late_series_and_dressrosa_impel_down(
    monkeypatch, client
) -> None:
    slug = await _seed_one_piece_slug(monkeypatch)

    names = _visible_names(client, slug, 1)

    assert names.isdisjoint(_MID_LATE_SERIES_NAMES)
    assert names.isdisjoint(_DRESSROSA_IMPEL_DOWN_NAMES)


# --- Checkpoint Episode 3 ---


async def test_checkpoint_episode_3_unlocks_early_allies_cleanly(monkeypatch, client) -> None:
    slug = await _seed_one_piece_slug(monkeypatch)

    names = _visible_names(client, slug, 3)

    assert names == {"Monkey D. Luffy", "Roronoa Zoro"}


# --- Checkpoint Episode 25 ---


async def test_checkpoint_episode_25_unlocks_early_saga_crew_in_sequence(monkeypatch, client) -> None:
    slug = await _seed_one_piece_slug(monkeypatch)

    names = _visible_names(client, slug, 25)

    assert names == {"Monkey D. Luffy", "Roronoa Zoro", "Nami", "Usopp", "Sanji"}
    assert names.isdisjoint(_MID_LATE_SERIES_NAMES)
    assert names.isdisjoint(_DRESSROSA_IMPEL_DOWN_NAMES)
    assert "Smoker" not in names  # Marine debuts ep. 138, still locked


# --- Checkpoint Episode 100+ ---


async def test_checkpoint_episode_100_unlocks_grand_line_additions(monkeypatch, client) -> None:
    slug = await _seed_one_piece_slug(monkeypatch)

    names = _visible_names(client, slug, 100)

    assert {"Tony Tony Chopper", "Nico Robin"} <= names
    assert "Smoker" not in names  # debuts ep. 138 — still beyond this checkpoint
    assert names.isdisjoint(_MID_LATE_SERIES_NAMES)
    assert names.isdisjoint(_DRESSROSA_IMPEL_DOWN_NAMES)


async def test_checkpoint_episode_150_unlocks_further_additions_progressively(
    monkeypatch, client
) -> None:
    slug = await _seed_one_piece_slug(monkeypatch)

    names_at_100 = _visible_names(client, slug, 100)
    names_at_150 = _visible_names(client, slug, 150)

    assert "Smoker" not in names_at_100
    assert "Smoker" in names_at_150
    assert names_at_100 < names_at_150  # strictly more characters unlocked, none lost
    assert names_at_150.isdisjoint(_MID_LATE_SERIES_NAMES)
    assert names_at_150.isdisjoint(_DRESSROSA_IMPEL_DOWN_NAMES)


# --- Unknown debut: permanent, checkpoint-independent exclusion ---


async def test_unknown_debut_character_is_excluded_at_the_final_episode(monkeypatch, client) -> None:
    """Proves exclusion isn't just "checkpoint too low" — even at the very last episode,
    a character with no confidently-determined debut never appears."""
    slug = await _seed_one_piece_slug(monkeypatch)

    names = _visible_names(client, slug, _TOTAL_EPISODES)

    assert "Ghost Extra" not in names


# --- No empty factions before their first member's introduction arc ---


async def test_faction_absent_until_its_first_member_has_debuted(monkeypatch, client) -> None:
    slug = await _seed_one_piece_slug(monkeypatch)

    assert "Marines & World Government" not in _faction_names(client, slug, 1)
    assert "Marines & World Government" not in _faction_names(client, slug, 137)
    assert "Marines & World Government" in _faction_names(client, slug, 138)


async def test_straw_hat_pirates_and_pirate_crews_present_from_episode_1(monkeypatch, client) -> None:
    slug = await _seed_one_piece_slug(monkeypatch)

    names = _faction_names(client, slug, 1)

    assert "Pirate Crews" in names
    assert "Straw Hat Pirates" in names


async def test_no_returned_faction_is_ever_empty(monkeypatch, client) -> None:
    slug = await _seed_one_piece_slug(monkeypatch)

    for episode in (1, 3, 25, 100, 150, _TOTAL_EPISODES):
        body = _dossier_body(client, slug, episode)
        character_faction_ids = {
            character["faction_id"] for character in body["characters"] if character["faction_id"]
        }
        faction_ids = {faction["id"] for faction in body["factions"]}

        for faction in body["factions"]:
            has_direct_member = faction["id"] in character_faction_ids
            has_surviving_child = any(
                other["parent_id"] == faction["id"] and other["id"] in faction_ids
                for other in body["factions"]
            )
            assert has_direct_member or has_surviving_child, (
                f"Empty faction {faction['name']!r} rendered at checkpoint S1E{episode}"
            )
