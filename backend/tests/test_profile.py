"""Tests for the user profile surface: profile payload generation (identity fields,
aggregate stats, per-anime watch checkpoints), password updates, and cascade
account deletion with password re-verification. See app/services/profile_service.py.
"""

import asyncio

from fastapi.testclient import TestClient

from app.models.anime import Anime
from tests.conftest import TestSessionLocal, _mark_verified


def _register(client: TestClient, email: str, password: str = "password123") -> str:
    response = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201
    asyncio.run(_mark_verified(email))

    login_response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


async def _create_anime(**kwargs) -> None:
    async with TestSessionLocal() as session:
        session.add(Anime(**kwargs))
        await session.commit()


def test_profile_payload_reports_stats_and_checkpoints(client: TestClient) -> None:
    asyncio.run(
        _create_anime(
            slug="profile-test-anime",
            title="Profile Test Anime",
            total_episodes=37,
            season_episode_counts=[25, 12],
            cover_image_url="https://example.com/cover.jpg",
        )
    )
    token = _register(client, "profile-payload@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    client.put(
        "/api/v1/me/watch-progress",
        json={"entries": [{"anime_slug": "profile-test-anime", "checkpoint": "S2E5"}]},
        headers=headers,
    )

    response = client.get("/api/v1/me/profile", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "profile-payload@example.com"
    assert body["is_verified"] is True
    assert body["created_at"]
    assert body["stats"] == {"total_series_tracked": 1, "total_episodes_watched": 30}
    assert body["checkpoints"] == [
        {
            "anime_slug": "profile-test-anime",
            "anime_title": "Profile Test Anime",
            "cover_image_url": "https://example.com/cover.jpg",
            "checkpoint": "S2E5",
            "current_episode": 30,
            "total_episodes": 37,
        }
    ]


def test_profile_payload_empty_when_nothing_tracked(client: TestClient) -> None:
    token = _register(client, "profile-empty@example.com")

    response = client.get("/api/v1/me/profile", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["stats"] == {"total_series_tracked": 0, "total_episodes_watched": 0}
    assert body["checkpoints"] == []


def test_profile_rejects_unauthenticated_request(client: TestClient) -> None:
    response = client.get("/api/v1/me/profile")

    assert response.status_code == 401


def test_update_password_succeeds_with_correct_current_password(client: TestClient) -> None:
    token = _register(client, "pw-update@example.com", password="old-password123")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(
        "/api/v1/me/password",
        json={"current_password": "old-password123", "new_password": "new-password456"},
        headers=headers,
    )

    assert response.status_code == 200

    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "pw-update@example.com", "password": "old-password123"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "pw-update@example.com", "password": "new-password456"},
    )
    assert new_login.status_code == 200


def test_update_password_rejects_wrong_current_password(client: TestClient) -> None:
    token = _register(client, "pw-update-wrong@example.com")

    response = client.put(
        "/api/v1/me/password",
        json={"current_password": "not-the-real-password", "new_password": "new-password456"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_update_password_rejects_short_new_password(client: TestClient) -> None:
    token = _register(client, "pw-update-short@example.com", password="password123")

    response = client.put(
        "/api/v1/me/password",
        json={"current_password": "password123", "new_password": "short"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_update_password_rejects_unauthenticated_request(client: TestClient) -> None:
    response = client.put(
        "/api/v1/me/password",
        json={"current_password": "whatever123", "new_password": "new-password456"},
    )

    assert response.status_code == 401


def test_delete_account_cascades_and_requires_correct_password(client: TestClient) -> None:
    asyncio.run(
        _create_anime(
            slug="delete-test-anime",
            title="Delete Test Anime",
            total_episodes=12,
            season_episode_counts=[12],
        )
    )
    token = _register(client, "delete-account@example.com", password="delete-me-123")
    headers = {"Authorization": f"Bearer {token}"}
    client.put(
        "/api/v1/me/watch-progress",
        json={"entries": [{"anime_slug": "delete-test-anime", "checkpoint": "S1E5"}]},
        headers=headers,
    )

    wrong_password_response = client.request(
        "DELETE", "/api/v1/me/account", json={"password": "not-it"}, headers=headers
    )
    assert wrong_password_response.status_code == 401

    response = client.request(
        "DELETE", "/api/v1/me/account", json={"password": "delete-me-123"}, headers=headers
    )
    assert response.status_code == 204

    # The token is now dead: get_current_user's post-decode DB lookup finds no
    # matching user row, which is this app's whole token-invalidation mechanism
    # since auth is a stateless JWT with no separate revocation list.
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 401

    # The email can be freshly re-registered — proof the row itself is gone, not
    # just its verification state reset.
    re_register = client.post(
        "/api/v1/auth/register",
        json={"email": "delete-account@example.com", "password": "password123"},
    )
    assert re_register.status_code == 201


def test_delete_account_rejects_unauthenticated_request(client: TestClient) -> None:
    response = client.request("DELETE", "/api/v1/me/account", json={"password": "whatever123"})

    assert response.status_code == 401
