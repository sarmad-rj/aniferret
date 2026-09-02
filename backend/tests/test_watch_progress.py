"""Tests for per-user watch-progress persistence: the piece that lets a logged-in
user's checkpoint survive across devices/sessions instead of only living in
localStorage (guest mode) — see app/services/watch_progress_service.py.
"""

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register", json={"email": email, "password": "password123"}
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def test_read_watch_progress_starts_empty(client: TestClient) -> None:
    token = _register(client, "progress-empty@example.com")

    response = client.get(
        "/api/v1/me/watch-progress", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["entries"] == []


def test_write_then_read_round_trips(client: TestClient) -> None:
    token = _register(client, "progress-roundtrip@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    write_response = client.put(
        "/api/v1/me/watch-progress",
        json={"entries": [{"anime_slug": "code-geass", "checkpoint": "S1E12"}]},
        headers=headers,
    )
    assert write_response.status_code == 200
    assert write_response.json()["entries"] == [
        {"anime_slug": "code-geass", "checkpoint": "S1E12"}
    ]

    read_response = client.get("/api/v1/me/watch-progress", headers=headers)
    assert read_response.json()["entries"] == [
        {"anime_slug": "code-geass", "checkpoint": "S1E12"}
    ]


def test_write_upserts_rather_than_duplicating(client: TestClient) -> None:
    token = _register(client, "progress-upsert@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    client.put(
        "/api/v1/me/watch-progress",
        json={"entries": [{"anime_slug": "code-geass", "checkpoint": "S1E1"}]},
        headers=headers,
    )
    response = client.put(
        "/api/v1/me/watch-progress",
        json={"entries": [{"anime_slug": "code-geass", "checkpoint": "S1E12"}]},
        headers=headers,
    )

    assert response.status_code == 200
    entries = response.json()["entries"]
    assert len(entries) == 1
    assert entries[0]["checkpoint"] == "S1E12"


def test_write_rejects_unknown_anime_slug(client: TestClient) -> None:
    token = _register(client, "progress-unknown-anime@example.com")

    response = client.put(
        "/api/v1/me/watch-progress",
        json={"entries": [{"anime_slug": "no-such-anime", "checkpoint": "S1E1"}]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_read_rejects_unauthenticated_request(client: TestClient) -> None:
    response = client.get("/api/v1/me/watch-progress")

    assert response.status_code == 401


def test_write_rejects_unauthenticated_request(client: TestClient) -> None:
    response = client.put(
        "/api/v1/me/watch-progress",
        json={"entries": [{"anime_slug": "code-geass", "checkpoint": "S1E1"}]},
    )

    assert response.status_code == 401


def test_progress_is_isolated_per_user(client: TestClient) -> None:
    token_a = _register(client, "progress-user-a@example.com")
    token_b = _register(client, "progress-user-b@example.com")

    client.put(
        "/api/v1/me/watch-progress",
        json={"entries": [{"anime_slug": "code-geass", "checkpoint": "S1E20"}]},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    response_b = client.get(
        "/api/v1/me/watch-progress", headers={"Authorization": f"Bearer {token_b}"}
    )

    assert response_b.json()["entries"] == []
