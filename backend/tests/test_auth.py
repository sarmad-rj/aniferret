"""Tests for JWT auth: registration, login, and /auth/me — the whole app must stay
guest-accessible (see test_group_mode.py's unauthenticated-request tests for the one
endpoint that does gate on this), so these only cover the auth surface itself.

Registration no longer doubles as login (it starts an unverified account and emails
a verification link) — see test_email_auth.py for the verify/reset flows themselves.
These tests use the `_mark_verified` conftest helper to get past that step directly
where a test just needs a working logged-in user, not to re-test verification.
"""

import asyncio

from fastapi.testclient import TestClient

from tests.conftest import _mark_verified


def test_register_creates_unverified_account(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "new-user@example.com", "password": "password123"},
    )

    assert response.status_code == 201
    body = response.json()
    assert "check your email" in body["message"].lower()
    assert "access_token" not in body


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "duplicate@example.com", "password": "password123"},
    )
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "duplicate@example.com", "password": "different-password"},
    )

    assert response.status_code == 409


def test_register_rejects_short_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "short-pw@example.com", "password": "short"},
    )

    assert response.status_code == 422


async def _register_and_verify(client: TestClient, email: str, password: str = "password123") -> None:
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    await _mark_verified(email)


def test_login_succeeds_with_correct_credentials(client: TestClient) -> None:
    asyncio.run(_register_and_verify(client, "login-success@example.com"))

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login-success@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_rejects_wrong_password(client: TestClient) -> None:
    asyncio.run(_register_and_verify(client, "login-wrong-pw@example.com"))

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login-wrong-pw@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_login_rejects_unknown_email(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "never-registered@example.com", "password": "password123"},
    )

    assert response.status_code == 401


def test_me_returns_current_user_with_valid_token(client: TestClient) -> None:
    asyncio.run(_register_and_verify(client, "me-endpoint@example.com"))
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "me-endpoint@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "me-endpoint@example.com"
    assert body["is_verified"] is True


def test_me_rejects_missing_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_rejects_garbage_token(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401
