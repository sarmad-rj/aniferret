"""Confirms the auth endpoints' rate limits actually engage. Every other test in
the suite runs with the limiter disabled (see conftest.py's autouse fixture --
TestClient requests all share one client address, and the suite calls /auth/
register and /auth/login far more than any real limit allows), so these are the
only tests that turn it back on.
"""

from fastapi.testclient import TestClient

from app.core.rate_limit import limiter


def test_register_endpoint_is_rate_limited(client: TestClient) -> None:
    limiter.enabled = True
    try:
        for i in range(5):
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"rate-limit-register-{i}@example.com",
                    "password": "password123",
                },
            )
            assert response.status_code == 201

        blocked_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "rate-limit-register-blocked@example.com",
                "password": "password123",
            },
        )
        assert blocked_response.status_code == 429
    finally:
        limiter.enabled = False


def test_login_endpoint_is_rate_limited(client: TestClient) -> None:
    limiter.enabled = True
    try:
        for _ in range(10):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "nonexistent-rate-limit@example.com", "password": "whatever123"},
            )
            assert response.status_code == 401

        blocked_response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent-rate-limit@example.com", "password": "whatever123"},
        )
        assert blocked_response.status_code == 429
    finally:
        limiter.enabled = False
