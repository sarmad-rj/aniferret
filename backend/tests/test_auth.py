"""Tests for JWT auth: registration, login, and /auth/me — the whole app must stay
guest-accessible (see test_group_mode.py's unauthenticated-request tests for the one
endpoint that does gate on this), so these only cover the auth surface itself.
"""

from fastapi.testclient import TestClient


def test_register_creates_account_and_returns_token(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "new-user@example.com", "password": "password123"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "new-user@example.com"
    assert "hashed_password" not in body["user"]


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


def test_login_succeeds_with_correct_credentials(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "login-success@example.com", "password": "password123"},
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login-success@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_rejects_wrong_password(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "login-wrong-pw@example.com", "password": "password123"},
    )

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
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "me-endpoint@example.com", "password": "password123", "display_name": "Me"},
    )
    token = register_response.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "me-endpoint@example.com"
    assert body["display_name"] == "Me"


def test_me_rejects_missing_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_rejects_garbage_token(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401
