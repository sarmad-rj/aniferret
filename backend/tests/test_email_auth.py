"""Email verification and password reset flow: registration issuing a token and
blocking login until verified, successful verification granting a JWT, expired/
malformed token rejection, and password reset end to end.

SMTP is never configured in tests (email_service fails silently — logged, not
raised — when unconfigured, per its own design), so these tests read the token
straight from the database rather than an inbox.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models.user import User
from tests.conftest import TestSessionLocal, _mark_verified


def _aware(dt: datetime) -> datetime:
    """SQLite round-trips DateTime(timezone=True) as naive — see auth_service._is_expired
    for the production-code equivalent of this same normalization."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


async def _get_user(email: str) -> User:
    async with TestSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one()


async def _expire_token(email: str, *, field: str) -> None:
    async with TestSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        setattr(user, field, datetime.now(timezone.utc) - timedelta(hours=1))
        await session.commit()


def test_register_issues_unexpired_verification_token(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "verify-issue@example.com", "password": "password123"},
    )

    user = asyncio.run(_get_user("verify-issue@example.com"))

    assert user.is_verified is False
    assert user.verification_token is not None
    assert user.verification_token_expires_at is not None
    assert _aware(user.verification_token_expires_at) > datetime.now(timezone.utc)


def test_login_blocked_until_verified(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "blocked-login@example.com", "password": "password123"},
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "blocked-login@example.com", "password": "password123"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["message"] == (
        "Please verify your email address before logging in."
    )


def test_verify_email_grants_valid_jwt_and_unlocks_login(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "verify-success@example.com", "password": "password123"},
    )
    user = asyncio.run(_get_user("verify-success@example.com"))
    raw_token = user.verification_token

    response = client.post("/api/v1/auth/verify-email", json={"token": raw_token})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["user"]["is_verified"] is True

    # The JWT actually works against a protected endpoint.
    me_response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "verify-success@example.com"

    # And login now succeeds, since verification cleared the block.
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "verify-success@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200


def test_verify_email_rejects_malformed_token(client: TestClient) -> None:
    response = client.post("/api/v1/auth/verify-email", json={"token": "not-a-real-token"})

    assert response.status_code == 400


def test_verify_email_rejects_expired_token(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "verify-expired@example.com", "password": "password123"},
    )
    asyncio.run(_expire_token("verify-expired@example.com", field="verification_token_expires_at"))
    user = asyncio.run(_get_user("verify-expired@example.com"))

    response = client.post("/api/v1/auth/verify-email", json={"token": user.verification_token})

    assert response.status_code == 400
    user_after = asyncio.run(_get_user("verify-expired@example.com"))
    assert user_after.is_verified is False


def test_verify_email_token_is_single_use(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "verify-once@example.com", "password": "password123"},
    )
    user = asyncio.run(_get_user("verify-once@example.com"))
    raw_token = user.verification_token

    first = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    second = client.post("/api/v1/auth/verify-email", json={"token": raw_token})

    assert first.status_code == 200
    assert second.status_code == 400


def test_resend_verification_always_returns_200_for_unknown_email(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/resend-verification", json={"email": "never-registered-resend@example.com"}
    )

    assert response.status_code == 200
    assert "verification link has been sent" in response.json()["message"].lower()


def test_resend_verification_issues_a_fresh_token(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "resend-fresh-token@example.com", "password": "password123"},
    )
    original_token = asyncio.run(_get_user("resend-fresh-token@example.com")).verification_token

    response = client.post(
        "/api/v1/auth/resend-verification", json={"email": "resend-fresh-token@example.com"}
    )

    assert response.status_code == 200
    user_after = asyncio.run(_get_user("resend-fresh-token@example.com"))
    assert user_after.verification_token is not None
    assert user_after.verification_token != original_token
    assert _aware(user_after.verification_token_expires_at) > datetime.now(timezone.utc)


def test_resend_verification_new_token_actually_verifies(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "resend-then-verify@example.com", "password": "password123"},
    )
    client.post(
        "/api/v1/auth/resend-verification", json={"email": "resend-then-verify@example.com"}
    )
    new_token = asyncio.run(_get_user("resend-then-verify@example.com")).verification_token

    response = client.post("/api/v1/auth/verify-email", json={"token": new_token})

    assert response.status_code == 200
    assert response.json()["user"]["is_verified"] is True


def test_resend_verification_invalidates_the_previous_token(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "resend-invalidates-old@example.com", "password": "password123"},
    )
    original_token = asyncio.run(_get_user("resend-invalidates-old@example.com")).verification_token

    client.post(
        "/api/v1/auth/resend-verification", json={"email": "resend-invalidates-old@example.com"}
    )

    response = client.post("/api/v1/auth/verify-email", json={"token": original_token})

    assert response.status_code == 400


def test_resend_verification_does_not_alter_an_already_verified_account(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "resend-already-verified@example.com", "password": "password123"},
    )
    asyncio.run(_mark_verified("resend-already-verified@example.com"))
    token_before = asyncio.run(_get_user("resend-already-verified@example.com")).verification_token

    response = client.post(
        "/api/v1/auth/resend-verification", json={"email": "resend-already-verified@example.com"}
    )

    assert response.status_code == 200
    token_after = asyncio.run(_get_user("resend-already-verified@example.com")).verification_token
    assert token_after == token_before


def test_forgot_password_always_returns_200_for_unknown_email(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/forgot-password", json={"email": "never-registered@example.com"}
    )

    assert response.status_code == 200
    assert "reset link has been sent" in response.json()["message"].lower()


def test_forgot_password_generates_token_for_known_email(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "forgot-pw@example.com", "password": "password123"},
    )

    response = client.post("/api/v1/auth/forgot-password", json={"email": "forgot-pw@example.com"})

    assert response.status_code == 200
    user = asyncio.run(_get_user("forgot-pw@example.com"))
    assert user.reset_password_token is not None
    assert user.reset_password_token_expires_at is not None
    assert _aware(user.reset_password_token_expires_at) <= datetime.now(timezone.utc) + timedelta(
        hours=1, minutes=1
    )


def test_reset_password_updates_password_and_allows_login(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "reset-success@example.com", "password": "old-password123"},
    )
    asyncio.run(_mark_verified("reset-success@example.com"))
    client.post("/api/v1/auth/forgot-password", json={"email": "reset-success@example.com"})
    user = asyncio.run(_get_user("reset-success@example.com"))
    raw_token = user.reset_password_token

    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "new-password456"},
    )

    assert response.status_code == 200

    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "reset-success@example.com", "password": "old-password123"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "reset-success@example.com", "password": "new-password456"},
    )
    assert new_login.status_code == 200


def test_reset_password_rejects_malformed_token(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "not-a-real-token", "new_password": "whatever123"},
    )

    assert response.status_code == 400


def test_reset_password_rejects_expired_token(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "reset-expired@example.com", "password": "password123"},
    )
    client.post("/api/v1/auth/forgot-password", json={"email": "reset-expired@example.com"})
    user = asyncio.run(_get_user("reset-expired@example.com"))
    raw_token = user.reset_password_token

    asyncio.run(_expire_token("reset-expired@example.com", field="reset_password_token_expires_at"))

    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "whatever123"},
    )

    assert response.status_code == 400
