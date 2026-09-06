"""Tests for the admin surface: admin-vs-regular-user gating (get_current_admin),
the anime inventory endpoint with per-anime character/fact counts, cascade delete,
user management (list/verify/delete with a self-delete guard), the data-integrity
report, and that anime import is no longer reachable without admin auth. See
app/services/admin_service.py and app/api/v1/dependencies.get_current_admin.
"""

import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models.anime import Anime
from app.models.character import Character
from app.models.faction import Faction
from app.models.temporal_fact import TemporalFact
from app.models.user import User
from tests.conftest import TestSessionLocal, _mark_verified


def _register_and_login(client: TestClient, email: str, password: str = "password123") -> str:
    response = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201
    asyncio.run(_mark_verified(email))

    login_response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


async def _create_anime(**kwargs) -> int:
    async with TestSessionLocal() as session:
        anime = Anime(**kwargs)
        session.add(anime)
        await session.commit()
        await session.refresh(anime)
        return anime.id


async def _create_character(**kwargs) -> int:
    async with TestSessionLocal() as session:
        character = Character(**kwargs)
        session.add(character)
        await session.commit()
        await session.refresh(character)
        return character.id


async def _create_faction(**kwargs) -> int:
    async with TestSessionLocal() as session:
        faction = Faction(**kwargs)
        session.add(faction)
        await session.commit()
        await session.refresh(faction)
        return faction.id


async def _create_fact(**kwargs) -> int:
    async with TestSessionLocal() as session:
        fact = TemporalFact(**kwargs)
        session.add(fact)
        await session.commit()
        await session.refresh(fact)
        return fact.fact_id


async def _get_character_first_revealed_at(character_id: int) -> str:
    async with TestSessionLocal() as session:
        character = await session.get(Character, character_id)
        return character.first_revealed_at


async def _get_character_faction_id(character_id: int) -> int | None:
    async with TestSessionLocal() as session:
        character = await session.get(Character, character_id)
        return character.faction_id


async def _get_fact_field(fact_id: int, field_name: str) -> str | None:
    async with TestSessionLocal() as session:
        fact = await session.get(TemporalFact, fact_id)
        return getattr(fact, field_name)


async def _get_user_id(email: str) -> int:
    async with TestSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one().id


def test_login_reports_is_admin_true_for_admin_account(client: TestClient, admin_auth_token: str) -> None:
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_auth_token}"}
    )

    assert response.status_code == 200
    assert response.json()["is_admin"] is True


def test_login_reports_is_admin_false_for_regular_account(client: TestClient) -> None:
    token = _register_and_login(client, "regular-user-admin-check@example.com")

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["is_admin"] is False


def test_admin_anime_list_rejects_unauthenticated_request(client: TestClient) -> None:
    response = client.get("/api/v1/admin/anime")

    assert response.status_code == 401


def test_admin_anime_list_rejects_non_admin_user(client: TestClient) -> None:
    token = _register_and_login(client, "non-admin-anime-list@example.com")

    response = client.get(
        "/api/v1/admin/anime", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_admin_anime_list_returns_counts_for_admin(client: TestClient, admin_auth_token: str) -> None:
    response = client.get(
        "/api/v1/admin/anime", headers={"Authorization": f"Bearer {admin_auth_token}"}
    )

    assert response.status_code == 200
    entries = {entry["slug"]: entry for entry in response.json()}
    # The shared "code-geass" fixture anime seeded in conftest.py has exactly 2
    # characters (Lelouch, Suzaku) and 2 TemporalFacts.
    assert entries["code-geass"]["character_count"] == 2
    assert entries["code-geass"]["fact_count"] == 2
    assert entries["code-geass"]["title"] == "Code Geass"


def test_admin_anime_delete_removes_row(client: TestClient, admin_auth_token: str) -> None:
    anime_id = asyncio.run(
        _create_anime(slug="admin-delete-test", title="Admin Delete Test", total_episodes=12)
    )
    headers = {"Authorization": f"Bearer {admin_auth_token}"}

    delete_response = client.delete(f"/api/v1/admin/anime/{anime_id}", headers=headers)
    assert delete_response.status_code == 204

    list_response = client.get("/api/v1/admin/anime", headers=headers)
    slugs = [entry["slug"] for entry in list_response.json()]
    assert "admin-delete-test" not in slugs


def test_admin_anime_delete_rejects_non_admin_user(client: TestClient) -> None:
    anime_id = asyncio.run(
        _create_anime(slug="admin-delete-guard", title="Admin Delete Guard", total_episodes=12)
    )
    token = _register_and_login(client, "non-admin-delete@example.com")

    response = client.delete(
        f"/api/v1/admin/anime/{anime_id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_admin_anime_delete_returns_404_for_unknown_id(client: TestClient, admin_auth_token: str) -> None:
    response = client.delete(
        "/api/v1/admin/anime/999999",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_import_anime_rejects_unauthenticated_request(client: TestClient) -> None:
    response = client.post("/api/v1/anime/import", json={"query": "whatever"})

    assert response.status_code == 401


def test_import_anime_rejects_non_admin_user(client: TestClient) -> None:
    token = _register_and_login(client, "non-admin-import@example.com")

    response = client.post(
        "/api/v1/anime/import",
        json={"query": "whatever"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_admin_users_list_rejects_unauthenticated_request(client: TestClient) -> None:
    response = client.get("/api/v1/admin/users")

    assert response.status_code == 401


def test_admin_users_list_rejects_non_admin_user(client: TestClient) -> None:
    token = _register_and_login(client, "non-admin-users-list@example.com")

    response = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_admin_users_list_reports_verification_and_admin_status(
    client: TestClient, admin_auth_token: str
) -> None:
    _register_and_login(client, "users-list-target@example.com")

    response = client.get(
        "/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_auth_token}"}
    )

    assert response.status_code == 200
    entries = {entry["email"]: entry for entry in response.json()}
    assert entries["users-list-target@example.com"]["is_verified"] is True
    assert entries["users-list-target@example.com"]["is_admin"] is False
    assert entries["fixture-admin@example.com"]["is_admin"] is True


def test_admin_verify_user_unblocks_login(client: TestClient, admin_auth_token: str) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "needs-manual-verify@example.com", "password": "password123"},
    )
    user_id = asyncio.run(_get_user_id("needs-manual-verify@example.com"))
    headers = {"Authorization": f"Bearer {admin_auth_token}"}

    blocked_login = client.post(
        "/api/v1/auth/login",
        json={"email": "needs-manual-verify@example.com", "password": "password123"},
    )
    assert blocked_login.status_code == 403

    response = client.put(f"/api/v1/admin/users/{user_id}/verify", headers=headers)
    assert response.status_code == 200

    unblocked_login = client.post(
        "/api/v1/auth/login",
        json={"email": "needs-manual-verify@example.com", "password": "password123"},
    )
    assert unblocked_login.status_code == 200


def test_admin_verify_user_rejects_non_admin_user(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "verify-guard-target@example.com", "password": "password123"},
    )
    user_id = asyncio.run(_get_user_id("verify-guard-target@example.com"))
    token = _register_and_login(client, "verify-guard-caller@example.com")

    response = client.put(
        f"/api/v1/admin/users/{user_id}/verify",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_admin_verify_user_returns_404_for_unknown_id(
    client: TestClient, admin_auth_token: str
) -> None:
    response = client.put(
        "/api/v1/admin/users/999999/verify",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_admin_delete_user_removes_account(client: TestClient, admin_auth_token: str) -> None:
    token = _register_and_login(client, "admin-delete-user-target@example.com")
    user_id = asyncio.run(_get_user_id("admin-delete-user-target@example.com"))
    headers = {"Authorization": f"Bearer {admin_auth_token}"}

    response = client.delete(f"/api/v1/admin/users/{user_id}", headers=headers)
    assert response.status_code == 204

    # The deleted user's own token is now dead too -- same stateless-JWT
    # invalidation-via-missing-row mechanism as self-service account deletion.
    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 401


def test_admin_delete_user_rejects_non_admin_user(client: TestClient) -> None:
    _register_and_login(client, "delete-guard-target@example.com")
    user_id = asyncio.run(_get_user_id("delete-guard-target@example.com"))
    token = _register_and_login(client, "delete-guard-caller@example.com")

    response = client.delete(
        f"/api/v1/admin/users/{user_id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_admin_delete_user_rejects_deleting_self(
    client: TestClient, admin_auth_token: str
) -> None:
    admin_id = asyncio.run(_get_user_id("fixture-admin@example.com"))

    response = client.delete(
        f"/api/v1/admin/users/{admin_id}",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 409


def test_admin_delete_user_returns_404_for_unknown_id(
    client: TestClient, admin_auth_token: str
) -> None:
    response = client.delete(
        "/api/v1/admin/users/999999",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_data_integrity_rejects_unauthenticated_request(client: TestClient) -> None:
    response = client.get("/api/v1/admin/data-integrity")

    assert response.status_code == 401


def test_data_integrity_rejects_non_admin_user(client: TestClient) -> None:
    token = _register_and_login(client, "non-admin-integrity@example.com")

    response = client.get(
        "/api/v1/admin/data-integrity", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_data_integrity_flags_known_fixture_issues(
    client: TestClient, admin_auth_token: str
) -> None:
    response = client.get(
        "/api/v1/admin/data-integrity",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 200
    body = response.json()

    # The shared "code-geass" fixture anime (conftest.py) has no
    # season_episode_counts set, so it's expected to trip every category here --
    # exactly what a minimally-specified anime record looks like in practice.
    mismatch_slugs = {row["anime_slug"] for row in body["episode_count_mismatches"]}
    assert "code-geass" in mismatch_slugs

    no_faction = {
        (row["anime_slug"], row["character_name"])
        for row in body["characters_without_faction"]
    }
    assert ("code-geass", "Suzaku Kururugi") in no_faction

    out_of_range_labels = {
        (row["anime_slug"], row["entity_label"]) for row in body["out_of_range_checkpoints"]
    }
    assert ("code-geass", "Suzaku Kururugi") in out_of_range_labels


def test_data_integrity_does_not_flag_a_well_formed_anime(
    client: TestClient, admin_auth_token: str
) -> None:
    asyncio.run(
        _create_anime(
            slug="integrity-clean-anime",
            title="Integrity Clean Anime",
            total_episodes=24,
            season_episode_counts=[12, 12],
        )
    )

    response = client.get(
        "/api/v1/admin/data-integrity",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 200
    mismatch_slugs = {row["anime_slug"] for row in response.json()["episode_count_mismatches"]}
    assert "integrity-clean-anime" not in mismatch_slugs


def test_fix_episode_counts_corrects_a_mismatch(client: TestClient, admin_auth_token: str) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="fix-episode-counts",
            title="Fix Episode Counts",
            total_episodes=50,
            season_episode_counts=[],
        )
    )
    headers = {"Authorization": f"Bearer {admin_auth_token}"}

    response = client.patch(
        f"/api/v1/admin/anime/{anime_id}/episode-counts",
        json={"total_episodes": 25, "season_episode_counts": [12, 13]},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_episodes"] == 25

    report = client.get("/api/v1/admin/data-integrity", headers=headers).json()
    mismatch_slugs = {row["anime_slug"] for row in report["episode_count_mismatches"]}
    assert "fix-episode-counts" not in mismatch_slugs


def test_fix_episode_counts_rejects_a_submission_that_still_mismatches(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="fix-episode-counts-still-wrong",
            title="Fix Episode Counts Still Wrong",
            total_episodes=50,
            season_episode_counts=[],
        )
    )

    response = client.patch(
        f"/api/v1/admin/anime/{anime_id}/episode-counts",
        json={"total_episodes": 25, "season_episode_counts": [12, 12]},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 422


def test_fix_episode_counts_returns_404_for_unknown_anime(
    client: TestClient, admin_auth_token: str
) -> None:
    response = client.patch(
        "/api/v1/admin/anime/999999/episode-counts",
        json={"total_episodes": 12, "season_episode_counts": [12]},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_fix_episode_counts_rejects_non_admin_user(client: TestClient) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="fix-episode-counts-guard",
            title="Fix Episode Counts Guard",
            total_episodes=50,
            season_episode_counts=[],
        )
    )
    token = _register_and_login(client, "non-admin-fix-episode-counts@example.com")

    response = client.patch(
        f"/api/v1/admin/anime/{anime_id}/episode-counts",
        json={"total_episodes": 12, "season_episode_counts": [12]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_fix_episode_counts_rejects_unauthenticated_request(client: TestClient) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="fix-episode-counts-anon",
            title="Fix Episode Counts Anon",
            total_episodes=50,
            season_episode_counts=[],
        )
    )

    response = client.patch(
        f"/api/v1/admin/anime/{anime_id}/episode-counts",
        json={"total_episodes": 12, "season_episode_counts": [12]},
    )

    assert response.status_code == 401


def test_fix_character_checkpoint_corrects_an_out_of_range_value(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="fix-character-checkpoint",
            title="Fix Character Checkpoint",
            total_episodes=24,
            season_episode_counts=[12, 12],
        )
    )
    character_id = asyncio.run(
        _create_character(
            anime_id=anime_id, name="Out Of Range Guy", first_revealed_at="S5E1"
        )
    )
    headers = {"Authorization": f"Bearer {admin_auth_token}"}

    response = client.patch(
        f"/api/v1/admin/characters/{character_id}/checkpoint",
        json={"first_revealed_at": "S2E5"},
        headers=headers,
    )

    assert response.status_code == 200
    assert asyncio.run(_get_character_first_revealed_at(character_id)) == "S2E5"


def test_fix_character_checkpoint_rejects_a_value_that_is_still_out_of_range(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="fix-character-checkpoint-still-wrong",
            title="Fix Character Checkpoint Still Wrong",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )
    character_id = asyncio.run(
        _create_character(
            anime_id=anime_id, name="Still Wrong Guy", first_revealed_at="S5E1"
        )
    )

    response = client.patch(
        f"/api/v1/admin/characters/{character_id}/checkpoint",
        json={"first_revealed_at": "S3E1"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 422


def test_fix_character_checkpoint_returns_404_for_unknown_character(
    client: TestClient, admin_auth_token: str
) -> None:
    response = client.patch(
        "/api/v1/admin/characters/999999/checkpoint",
        json={"first_revealed_at": "S1E1"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_fix_character_checkpoint_rejects_non_admin_user(client: TestClient) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="fix-character-checkpoint-guard",
            title="Fix Character Checkpoint Guard",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )
    character_id = asyncio.run(
        _create_character(anime_id=anime_id, name="Guard Guy", first_revealed_at="S5E1")
    )
    token = _register_and_login(client, "non-admin-fix-character@example.com")

    response = client.patch(
        f"/api/v1/admin/characters/{character_id}/checkpoint",
        json={"first_revealed_at": "S1E1"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_fix_fact_checkpoint_corrects_an_out_of_range_value(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="fix-fact-checkpoint",
            title="Fix Fact Checkpoint",
            total_episodes=24,
            season_episode_counts=[12, 12],
        )
    )
    fact_id = asyncio.run(
        _create_fact(
            anime_id=anime_id,
            subject="Someone",
            predicate="does_something",
            object="A thing happens.",
            source_citation="S9E1",
            first_revealed_at="S9E1",
            confidence=0.9,
        )
    )
    headers = {"Authorization": f"Bearer {admin_auth_token}"}

    response = client.patch(
        f"/api/v1/admin/facts/{fact_id}/checkpoint",
        json={"field": "first_revealed_at", "checkpoint": "S1E6"},
        headers=headers,
    )

    assert response.status_code == 200
    assert asyncio.run(_get_fact_field(fact_id, "first_revealed_at")) == "S1E6"


def test_fix_fact_checkpoint_rejects_a_value_that_is_still_out_of_range(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="fix-fact-checkpoint-still-wrong",
            title="Fix Fact Checkpoint Still Wrong",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )
    fact_id = asyncio.run(
        _create_fact(
            anime_id=anime_id,
            subject="Someone",
            predicate="does_something",
            object="A thing happens.",
            source_citation="S9E1",
            first_revealed_at="S9E1",
            confidence=0.9,
        )
    )

    response = client.patch(
        f"/api/v1/admin/facts/{fact_id}/checkpoint",
        json={"field": "first_revealed_at", "checkpoint": "S4E1"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 422


def test_fix_fact_checkpoint_returns_404_for_unknown_fact(
    client: TestClient, admin_auth_token: str
) -> None:
    response = client.patch(
        "/api/v1/admin/facts/999999/checkpoint",
        json={"field": "first_revealed_at", "checkpoint": "S1E1"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_fix_fact_checkpoint_rejects_non_admin_user(client: TestClient) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="fix-fact-checkpoint-guard",
            title="Fix Fact Checkpoint Guard",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )
    fact_id = asyncio.run(
        _create_fact(
            anime_id=anime_id,
            subject="Someone",
            predicate="does_something",
            object="A thing happens.",
            source_citation="S9E1",
            first_revealed_at="S9E1",
            confidence=0.9,
        )
    )
    token = _register_and_login(client, "non-admin-fix-fact@example.com")

    response = client.patch(
        f"/api/v1/admin/facts/{fact_id}/checkpoint",
        json={"field": "first_revealed_at", "checkpoint": "S1E1"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_list_anime_factions_returns_that_animes_factions(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="factions-list-anime",
            title="Factions List Anime",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )
    asyncio.run(_create_faction(anime_id=anime_id, name="Alpha Faction"))
    asyncio.run(_create_faction(anime_id=anime_id, name="Beta Faction"))

    response = client.get(
        f"/api/v1/admin/anime/{anime_id}/factions",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 200
    names = {row["name"] for row in response.json()}
    assert names == {"Alpha Faction", "Beta Faction"}


def test_list_anime_factions_returns_404_for_unknown_anime(
    client: TestClient, admin_auth_token: str
) -> None:
    response = client.get(
        "/api/v1/admin/anime/999999/factions",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_list_anime_factions_rejects_non_admin_user(client: TestClient) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="factions-list-guard",
            title="Factions List Guard",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )
    token = _register_and_login(client, "non-admin-factions-list@example.com")

    response = client.get(
        f"/api/v1/admin/anime/{anime_id}/factions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_fix_character_faction_assigns_a_faction(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="fix-character-faction",
            title="Fix Character Faction",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )
    faction_id = asyncio.run(_create_faction(anime_id=anime_id, name="The Chosen Faction"))
    character_id = asyncio.run(
        _create_character(anime_id=anime_id, name="Factionless Guy", faction_id=None)
    )
    headers = {"Authorization": f"Bearer {admin_auth_token}"}

    response = client.patch(
        f"/api/v1/admin/characters/{character_id}/faction",
        json={"faction_id": faction_id},
        headers=headers,
    )

    assert response.status_code == 200
    assert asyncio.run(_get_character_faction_id(character_id)) == faction_id


def test_fix_character_faction_rejects_a_faction_from_a_different_anime(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_a_id = asyncio.run(
        _create_anime(
            slug="fix-character-faction-anime-a",
            title="Fix Character Faction Anime A",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )
    anime_b_id = asyncio.run(
        _create_anime(
            slug="fix-character-faction-anime-b",
            title="Fix Character Faction Anime B",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )
    foreign_faction_id = asyncio.run(_create_faction(anime_id=anime_b_id, name="Foreign Faction"))
    character_id = asyncio.run(
        _create_character(anime_id=anime_a_id, name="Mismatched Guy", faction_id=None)
    )

    response = client.patch(
        f"/api/v1/admin/characters/{character_id}/faction",
        json={"faction_id": foreign_faction_id},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 400


def test_fix_character_faction_returns_404_for_unknown_character(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="fix-character-faction-unknown-char",
            title="Fix Character Faction Unknown Char",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )
    faction_id = asyncio.run(_create_faction(anime_id=anime_id, name="Some Faction"))

    response = client.patch(
        "/api/v1/admin/characters/999999/faction",
        json={"faction_id": faction_id},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_fix_character_faction_returns_404_for_unknown_faction(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="fix-character-faction-unknown-faction",
            title="Fix Character Faction Unknown Faction",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )
    character_id = asyncio.run(
        _create_character(anime_id=anime_id, name="Waiting Guy", faction_id=None)
    )

    response = client.patch(
        f"/api/v1/admin/characters/{character_id}/faction",
        json={"faction_id": 999999},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_fix_character_faction_rejects_non_admin_user(client: TestClient) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="fix-character-faction-guard",
            title="Fix Character Faction Guard",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )
    faction_id = asyncio.run(_create_faction(anime_id=anime_id, name="Guarded Faction"))
    character_id = asyncio.run(
        _create_character(anime_id=anime_id, name="Guarded Guy", faction_id=None)
    )
    token = _register_and_login(client, "non-admin-fix-faction@example.com")

    response = client.patch(
        f"/api/v1/admin/characters/{character_id}/faction",
        json={"faction_id": faction_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_bulk_delete_anime_removes_all_selected(client: TestClient, admin_auth_token: str) -> None:
    anime_a = asyncio.run(
        _create_anime(slug="bulk-delete-anime-a", title="Bulk Delete Anime A", total_episodes=12)
    )
    anime_b = asyncio.run(
        _create_anime(slug="bulk-delete-anime-b", title="Bulk Delete Anime B", total_episodes=12)
    )
    headers = {"Authorization": f"Bearer {admin_auth_token}"}

    response = client.post(
        "/api/v1/admin/anime/bulk-delete", json={"ids": [anime_a, anime_b]}, headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body["deleted_ids"]) == {anime_a, anime_b}
    assert body["failed"] == []

    list_response = client.get("/api/v1/admin/anime", headers=headers)
    slugs = {entry["slug"] for entry in list_response.json()}
    assert "bulk-delete-anime-a" not in slugs
    assert "bulk-delete-anime-b" not in slugs


def test_bulk_delete_anime_reports_partial_failure(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="bulk-delete-anime-partial", title="Bulk Delete Anime Partial", total_episodes=12
        )
    )

    response = client.post(
        "/api/v1/admin/anime/bulk-delete",
        json={"ids": [anime_id, 999999]},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["deleted_ids"] == [anime_id]
    assert len(body["failed"]) == 1
    assert body["failed"][0]["id"] == "999999"


def test_bulk_delete_anime_rejects_non_admin_user(client: TestClient) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="bulk-delete-anime-guard", title="Bulk Delete Anime Guard", total_episodes=12
        )
    )
    token = _register_and_login(client, "non-admin-bulk-delete-anime@example.com")

    response = client.post(
        "/api/v1/admin/anime/bulk-delete",
        json={"ids": [anime_id]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_bulk_delete_anime_rejects_unauthenticated_request(client: TestClient) -> None:
    response = client.post("/api/v1/admin/anime/bulk-delete", json={"ids": [1]})

    assert response.status_code == 401


def test_bulk_delete_users_removes_all_selected(client: TestClient, admin_auth_token: str) -> None:
    _register_and_login(client, "bulk-delete-user-a@example.com")
    _register_and_login(client, "bulk-delete-user-b@example.com")
    user_a = asyncio.run(_get_user_id("bulk-delete-user-a@example.com"))
    user_b = asyncio.run(_get_user_id("bulk-delete-user-b@example.com"))
    headers = {"Authorization": f"Bearer {admin_auth_token}"}

    response = client.post(
        "/api/v1/admin/users/bulk-delete", json={"ids": [user_a, user_b]}, headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body["deleted_ids"]) == {user_a, user_b}
    assert body["failed"] == []


def test_bulk_delete_users_reports_self_delete_as_a_failure_without_blocking_others(
    client: TestClient, admin_auth_token: str
) -> None:
    admin_id = asyncio.run(_get_user_id("fixture-admin@example.com"))
    _register_and_login(client, "bulk-delete-user-with-self@example.com")
    other_user_id = asyncio.run(_get_user_id("bulk-delete-user-with-self@example.com"))

    response = client.post(
        "/api/v1/admin/users/bulk-delete",
        json={"ids": [admin_id, other_user_id]},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["deleted_ids"] == [other_user_id]
    assert len(body["failed"]) == 1
    assert body["failed"][0]["id"] == str(admin_id)


def test_bulk_delete_users_rejects_non_admin_user(client: TestClient) -> None:
    _register_and_login(client, "bulk-delete-user-guard-target@example.com")
    target_id = asyncio.run(_get_user_id("bulk-delete-user-guard-target@example.com"))
    token = _register_and_login(client, "non-admin-bulk-delete-users@example.com")

    response = client.post(
        "/api/v1/admin/users/bulk-delete",
        json={"ids": [target_id]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_bulk_delete_users_rejects_unauthenticated_request(client: TestClient) -> None:
    response = client.post("/api/v1/admin/users/bulk-delete", json={"ids": [1]})

    assert response.status_code == 401


def test_system_status_reports_smtp_configured_state(
    client: TestClient, admin_auth_token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Monkeypatched rather than asserted against the ambient real .env -- this
    # endpoint's whole point is to report whatever the real environment has, which
    # varies machine to machine, so the test controls it explicitly in both
    # directions instead of assuming a value.
    import app.api.v1.endpoints.admin as admin_endpoint

    class _ConfiguredSettings:
        smtp_host = "smtp.example.com"
        smtp_user = "user@example.com"
        smtp_password = "secret"

    class _UnconfiguredSettings:
        smtp_host = ""
        smtp_user = ""
        smtp_password = ""

    headers = {"Authorization": f"Bearer {admin_auth_token}"}

    monkeypatch.setattr(admin_endpoint, "get_settings", lambda: _ConfiguredSettings())
    configured_response = client.get("/api/v1/admin/system-status", headers=headers)
    assert configured_response.json()["smtp_configured"] is True

    monkeypatch.setattr(admin_endpoint, "get_settings", lambda: _UnconfiguredSettings())
    unconfigured_response = client.get("/api/v1/admin/system-status", headers=headers)
    assert unconfigured_response.json()["smtp_configured"] is False


def test_system_status_rejects_non_admin_user(client: TestClient) -> None:
    token = _register_and_login(client, "non-admin-system-status@example.com")

    response = client.get(
        "/api/v1/admin/system-status", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_system_status_rejects_unauthenticated_request(client: TestClient) -> None:
    response = client.get("/api/v1/admin/system-status")

    assert response.status_code == 401


def test_read_anime_detail_returns_full_metadata(client: TestClient, admin_auth_token: str) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="anime-detail-read",
            title="Anime Detail Read",
            total_episodes=12,
            season_episode_counts=[12],
            cover_image_url="https://example.com/cover.jpg",
            genres=["Action"],
            synopsis="A test synopsis.",
            score=7.5,
        )
    )

    response = client.get(
        f"/api/v1/admin/anime/{anime_id}/detail",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Anime Detail Read"
    assert body["cover_image_url"] == "https://example.com/cover.jpg"
    assert body["genres"] == ["Action"]
    assert body["synopsis"] == "A test synopsis."
    assert body["score"] == 7.5


def test_read_anime_detail_returns_404_for_unknown_anime(
    client: TestClient, admin_auth_token: str
) -> None:
    response = client.get(
        "/api/v1/admin/anime/999999/detail",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_read_anime_detail_rejects_non_admin_user(client: TestClient) -> None:
    anime_id = asyncio.run(
        _create_anime(slug="anime-detail-guard", title="Anime Detail Guard", total_episodes=12)
    )
    token = _register_and_login(client, "non-admin-anime-detail@example.com")

    response = client.get(
        f"/api/v1/admin/anime/{anime_id}/detail", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_update_anime_metadata_updates_descriptive_fields(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(slug="anime-metadata-update", title="Old Title", total_episodes=12)
    )
    headers = {"Authorization": f"Bearer {admin_auth_token}"}

    response = client.patch(
        f"/api/v1/admin/anime/{anime_id}/metadata",
        json={
            "title": "New Title",
            "cover_image_url": "https://example.com/new-cover.jpg",
            "genres": ["Drama", "Mystery"],
            "synopsis": "Updated synopsis.",
            "score": 8.2,
        },
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "New Title"
    assert body["genres"] == ["Drama", "Mystery"]
    assert body["score"] == 8.2

    detail_response = client.get(f"/api/v1/admin/anime/{anime_id}/detail", headers=headers)
    assert detail_response.json()["title"] == "New Title"


def test_update_anime_metadata_rejects_score_out_of_range(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(slug="anime-metadata-bad-score", title="Bad Score", total_episodes=12)
    )

    response = client.patch(
        f"/api/v1/admin/anime/{anime_id}/metadata",
        json={"title": "Bad Score", "genres": [], "score": 11},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 422


def test_update_anime_metadata_returns_404_for_unknown_anime(
    client: TestClient, admin_auth_token: str
) -> None:
    response = client.patch(
        "/api/v1/admin/anime/999999/metadata",
        json={"title": "Nope", "genres": []},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_update_anime_metadata_rejects_non_admin_user(client: TestClient) -> None:
    anime_id = asyncio.run(
        _create_anime(slug="anime-metadata-guard", title="Metadata Guard", total_episodes=12)
    )
    token = _register_and_login(client, "non-admin-anime-metadata@example.com")

    response = client.patch(
        f"/api/v1/admin/anime/{anime_id}/metadata",
        json={"title": "Nope", "genres": []},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_create_faction_succeeds_with_a_top_level_parent(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(slug="faction-create-anime", title="Faction Create Anime", total_episodes=12)
    )
    parent_id = asyncio.run(_create_faction(anime_id=anime_id, name="Parent Faction"))
    headers = {"Authorization": f"Bearer {admin_auth_token}"}

    response = client.post(
        f"/api/v1/admin/anime/{anime_id}/factions",
        json={"name": "Child Faction", "description": "A crew.", "parent_id": parent_id},
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Child Faction"
    assert body["parent_id"] == parent_id
    assert body["anime_id"] == anime_id


def test_create_faction_rejects_parent_from_a_different_anime(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_a = asyncio.run(_create_anime(slug="faction-create-a", title="A", total_episodes=12))
    anime_b = asyncio.run(_create_anime(slug="faction-create-b", title="B", total_episodes=12))
    foreign_parent_id = asyncio.run(_create_faction(anime_id=anime_b, name="Foreign Parent"))

    response = client.post(
        f"/api/v1/admin/anime/{anime_a}/factions",
        json={"name": "Child", "parent_id": foreign_parent_id},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 400


def test_create_faction_rejects_a_parent_that_is_itself_a_child(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(slug="faction-create-three-tier", title="Three Tier", total_episodes=12)
    )
    grandparent_id = asyncio.run(_create_faction(anime_id=anime_id, name="Grandparent"))
    parent_id = asyncio.run(
        _create_faction(anime_id=anime_id, name="Parent", parent_id=grandparent_id)
    )

    response = client.post(
        f"/api/v1/admin/anime/{anime_id}/factions",
        json={"name": "Grandchild", "parent_id": parent_id},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 400


def test_create_faction_returns_404_for_unknown_anime(
    client: TestClient, admin_auth_token: str
) -> None:
    response = client.post(
        "/api/v1/admin/anime/999999/factions",
        json={"name": "Orphan Faction"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_create_faction_rejects_non_admin_user(client: TestClient) -> None:
    anime_id = asyncio.run(
        _create_anime(slug="faction-create-guard", title="Faction Create Guard", total_episodes=12)
    )
    token = _register_and_login(client, "non-admin-faction-create@example.com")

    response = client.post(
        f"/api/v1/admin/anime/{anime_id}/factions",
        json={"name": "Nope"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_update_faction_rejects_being_its_own_parent(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(slug="faction-update-self-parent", title="Self Parent", total_episodes=12)
    )
    faction_id = asyncio.run(_create_faction(anime_id=anime_id, name="Faction"))

    response = client.patch(
        f"/api/v1/admin/factions/{faction_id}",
        json={"name": "Faction", "parent_id": faction_id},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 400


def test_update_faction_returns_404_for_unknown_faction(
    client: TestClient, admin_auth_token: str
) -> None:
    response = client.patch(
        "/api/v1/admin/factions/999999",
        json={"name": "Nope"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_update_faction_rejects_non_admin_user(client: TestClient) -> None:
    anime_id = asyncio.run(
        _create_anime(slug="faction-update-guard", title="Faction Update Guard", total_episodes=12)
    )
    faction_id = asyncio.run(_create_faction(anime_id=anime_id, name="Faction"))
    token = _register_and_login(client, "non-admin-faction-update@example.com")

    response = client.patch(
        f"/api/v1/admin/factions/{faction_id}",
        json={"name": "Renamed"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_delete_faction_unassigns_its_characters_and_deletes_child_factions(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(slug="faction-delete-cascade", title="Faction Delete Cascade", total_episodes=12)
    )
    parent_id = asyncio.run(_create_faction(anime_id=anime_id, name="Parent"))
    child_id = asyncio.run(_create_faction(anime_id=anime_id, name="Child", parent_id=parent_id))
    character_on_parent = asyncio.run(
        _create_character(anime_id=anime_id, name="On Parent", faction_id=parent_id)
    )
    character_on_child = asyncio.run(
        _create_character(anime_id=anime_id, name="On Child", faction_id=child_id)
    )
    headers = {"Authorization": f"Bearer {admin_auth_token}"}

    response = client.request(
        "DELETE", f"/api/v1/admin/factions/{parent_id}", headers=headers
    )

    assert response.status_code == 204
    assert asyncio.run(_get_character_faction_id(character_on_parent)) is None
    assert asyncio.run(_get_character_faction_id(character_on_child)) is None

    factions_response = client.get(f"/api/v1/admin/anime/{anime_id}/factions", headers=headers)
    remaining_names = {row["name"] for row in factions_response.json()}
    assert "Parent" not in remaining_names
    assert "Child" not in remaining_names


def test_delete_faction_returns_404_for_unknown_faction(
    client: TestClient, admin_auth_token: str
) -> None:
    response = client.request(
        "DELETE",
        "/api/v1/admin/factions/999999",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_delete_faction_rejects_non_admin_user(client: TestClient) -> None:
    anime_id = asyncio.run(
        _create_anime(slug="faction-delete-guard", title="Faction Delete Guard", total_episodes=12)
    )
    faction_id = asyncio.run(_create_faction(anime_id=anime_id, name="Faction"))
    token = _register_and_login(client, "non-admin-faction-delete@example.com")

    response = client.request(
        "DELETE",
        f"/api/v1/admin/factions/{faction_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_list_anime_characters_returns_that_animes_roster(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="characters-list-anime",
            title="Characters List Anime",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )
    asyncio.run(_create_character(anime_id=anime_id, name="Alpha", first_revealed_at="S1E1"))
    asyncio.run(_create_character(anime_id=anime_id, name="Beta", first_revealed_at="S1E2"))

    response = client.get(
        f"/api/v1/admin/anime/{anime_id}/characters",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 200
    names = {row["name"] for row in response.json()}
    assert names == {"Alpha", "Beta"}


def test_list_anime_characters_returns_404_for_unknown_anime(
    client: TestClient, admin_auth_token: str
) -> None:
    response = client.get(
        "/api/v1/admin/anime/999999/characters",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_create_character_succeeds_with_valid_checkpoint_and_faction(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="character-create-anime",
            title="Character Create Anime",
            total_episodes=24,
            season_episode_counts=[12, 12],
        )
    )
    faction_id = asyncio.run(_create_faction(anime_id=anime_id, name="A Faction"))
    headers = {"Authorization": f"Bearer {admin_auth_token}"}

    response = client.post(
        f"/api/v1/admin/anime/{anime_id}/characters",
        json={
            "name": "New Character",
            "role": "Main",
            "faction_id": faction_id,
            "first_revealed_at": "S2E5",
        },
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "New Character"
    assert body["faction_id"] == faction_id
    assert body["first_revealed_at"] == "S2E5"


def test_create_character_rejects_an_out_of_range_checkpoint(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="character-create-bad-checkpoint",
            title="Character Create Bad Checkpoint",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )

    response = client.post(
        f"/api/v1/admin/anime/{anime_id}/characters",
        json={"name": "Bad Checkpoint Guy", "first_revealed_at": "S5E1"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 422


def test_create_character_rejects_a_faction_from_a_different_anime(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_a = asyncio.run(_create_anime(slug="character-create-anime-a", title="A", total_episodes=12))
    anime_b = asyncio.run(_create_anime(slug="character-create-anime-b", title="B", total_episodes=12))
    foreign_faction_id = asyncio.run(_create_faction(anime_id=anime_b, name="Foreign Faction"))

    response = client.post(
        f"/api/v1/admin/anime/{anime_a}/characters",
        json={"name": "Mismatched Guy", "faction_id": foreign_faction_id, "first_revealed_at": "S1E1"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 422


def test_create_character_returns_404_for_unknown_anime(
    client: TestClient, admin_auth_token: str
) -> None:
    response = client.post(
        "/api/v1/admin/anime/999999/characters",
        json={"name": "Nope"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_create_character_rejects_non_admin_user(client: TestClient) -> None:
    anime_id = asyncio.run(
        _create_anime(slug="character-create-guard", title="Character Create Guard", total_episodes=12)
    )
    token = _register_and_login(client, "non-admin-character-create@example.com")

    response = client.post(
        f"/api/v1/admin/anime/{anime_id}/characters",
        json={"name": "Nope"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_update_character_updates_descriptive_fields(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="character-update-anime",
            title="Character Update Anime",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )
    character_id = asyncio.run(
        _create_character(anime_id=anime_id, name="Old Name", first_revealed_at="S1E1")
    )
    headers = {"Authorization": f"Bearer {admin_auth_token}"}

    response = client.patch(
        f"/api/v1/admin/characters/{character_id}",
        json={
            "name": "New Name",
            "role": "Supporting",
            "backstory": "A new backstory.",
            "first_revealed_at": "S1E6",
        },
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New Name"
    assert body["role"] == "Supporting"
    assert body["backstory"] == "A new backstory."
    assert body["first_revealed_at"] == "S1E6"


def test_update_character_rejects_an_out_of_range_checkpoint(
    client: TestClient, admin_auth_token: str
) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="character-update-bad-checkpoint",
            title="Character Update Bad Checkpoint",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )
    character_id = asyncio.run(
        _create_character(anime_id=anime_id, name="Guy", first_revealed_at="S1E1")
    )

    response = client.patch(
        f"/api/v1/admin/characters/{character_id}",
        json={"name": "Guy", "first_revealed_at": "S9E1"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 422


def test_update_character_returns_404_for_unknown_character(
    client: TestClient, admin_auth_token: str
) -> None:
    response = client.patch(
        "/api/v1/admin/characters/999999",
        json={"name": "Nope"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_update_character_rejects_non_admin_user(client: TestClient) -> None:
    anime_id = asyncio.run(
        _create_anime(
            slug="character-update-guard",
            title="Character Update Guard",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )
    character_id = asyncio.run(
        _create_character(anime_id=anime_id, name="Guy", first_revealed_at="S1E1")
    )
    token = _register_and_login(client, "non-admin-character-update@example.com")

    response = client.patch(
        f"/api/v1/admin/characters/{character_id}",
        json={"name": "Nope"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_delete_character_removes_the_row(client: TestClient, admin_auth_token: str) -> None:
    anime_id = asyncio.run(
        _create_anime(slug="character-delete-anime", title="Character Delete Anime", total_episodes=12)
    )
    character_id = asyncio.run(
        _create_character(anime_id=anime_id, name="Doomed Guy", first_revealed_at="S1E1")
    )
    headers = {"Authorization": f"Bearer {admin_auth_token}"}

    response = client.request(
        "DELETE", f"/api/v1/admin/characters/{character_id}", headers=headers
    )

    assert response.status_code == 204

    list_response = client.get(f"/api/v1/admin/anime/{anime_id}/characters", headers=headers)
    names = {row["name"] for row in list_response.json()}
    assert "Doomed Guy" not in names


def test_delete_character_returns_404_for_unknown_character(
    client: TestClient, admin_auth_token: str
) -> None:
    response = client.request(
        "DELETE",
        "/api/v1/admin/characters/999999",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert response.status_code == 404


def test_delete_character_rejects_non_admin_user(client: TestClient) -> None:
    anime_id = asyncio.run(
        _create_anime(slug="character-delete-guard", title="Character Delete Guard", total_episodes=12)
    )
    character_id = asyncio.run(
        _create_character(anime_id=anime_id, name="Guy", first_revealed_at="S1E1")
    )
    token = _register_and_login(client, "non-admin-character-delete@example.com")

    response = client.request(
        "DELETE",
        f"/api/v1/admin/characters/{character_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
