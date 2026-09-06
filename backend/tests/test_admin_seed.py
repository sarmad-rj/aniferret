"""Covers app.db.seed.seed_admin_user() and main(admin_only=...) — the only path by
which a deployed environment gets an admin account, since there is no public
self-service "register as admin" endpoint. Wired into backend/Dockerfile's CMD as
`python -m app.db.seed --admin-only`, run on every boot after migrations.
"""

from sqlalchemy import select

from app.core.security import hash_password
from app.db import seed as seed_module
from app.models import User
from tests.conftest import TestSessionLocal


class _AdminEnvSettings:
    def __init__(self, admin_email: str = "", admin_password: str = "") -> None:
        self.admin_email = admin_email
        self.admin_password = admin_password


async def _fetch_user(email: str) -> User | None:
    async with TestSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


async def test_seed_admin_user_noop_when_unconfigured(monkeypatch) -> None:
    monkeypatch.setattr(seed_module, "get_settings", lambda: _AdminEnvSettings())

    async with TestSessionLocal() as session:
        await seed_module.seed_admin_user(session)

    assert await _fetch_user("") is None


async def test_seed_admin_user_creates_account_when_configured(monkeypatch) -> None:
    monkeypatch.setattr(
        seed_module,
        "get_settings",
        lambda: _AdminEnvSettings("boss@example.com", "supersecret123"),
    )

    async with TestSessionLocal() as session:
        await seed_module.seed_admin_user(session)

    admin = await _fetch_user("boss@example.com")
    assert admin is not None
    assert admin.is_admin is True
    assert admin.is_verified is True
    assert admin.hashed_password != "supersecret123"


async def test_seed_admin_user_is_idempotent_and_never_overwrites_password(monkeypatch) -> None:
    monkeypatch.setattr(
        seed_module,
        "get_settings",
        lambda: _AdminEnvSettings("idempotent-admin@example.com", "first-password"),
    )
    async with TestSessionLocal() as session:
        await seed_module.seed_admin_user(session)
    original_hash = (await _fetch_user("idempotent-admin@example.com")).hashed_password

    # Re-running with a *different* configured password must not overwrite the
    # existing hash — only the admin's own account-settings flow may change it.
    monkeypatch.setattr(
        seed_module,
        "get_settings",
        lambda: _AdminEnvSettings("idempotent-admin@example.com", "a-different-password"),
    )
    async with TestSessionLocal() as session:
        await seed_module.seed_admin_user(session)

    admin = await _fetch_user("idempotent-admin@example.com")
    assert admin.hashed_password == original_hash
    assert admin.is_admin is True


async def test_seed_admin_user_promotes_an_existing_non_admin_account(monkeypatch) -> None:
    async with TestSessionLocal() as session:
        session.add(
            User(
                email="promote-me@example.com",
                hashed_password=hash_password("whatever"),
                is_verified=True,
                is_admin=False,
            )
        )
        await session.commit()

    monkeypatch.setattr(
        seed_module,
        "get_settings",
        lambda: _AdminEnvSettings("promote-me@example.com", "ignored-account-already-exists"),
    )
    async with TestSessionLocal() as session:
        await seed_module.seed_admin_user(session)

    admin = await _fetch_user("promote-me@example.com")
    assert admin.is_admin is True


async def test_main_admin_only_skips_catalog_seed(monkeypatch) -> None:
    """The Dockerfile's `--admin-only` flag must not re-run seed_all() — the
    container's catalog data arrives via app.core.bootstrap's volume copy instead,
    so main(admin_only=True) should touch only the admin account."""
    calls: list[str] = []

    async def _fake_seed_all(session) -> None:
        calls.append("seed_all")

    async def _fake_seed_admin_user(session) -> None:
        calls.append("seed_admin_user")

    monkeypatch.setattr(seed_module, "seed_all", _fake_seed_all)
    monkeypatch.setattr(seed_module, "seed_admin_user", _fake_seed_admin_user)
    monkeypatch.setattr(seed_module, "AsyncSessionLocal", TestSessionLocal)

    await seed_module.main(admin_only=True)

    assert calls == ["seed_admin_user"]


async def test_main_without_admin_only_runs_both(monkeypatch) -> None:
    calls: list[str] = []

    async def _fake_seed_all(session) -> None:
        calls.append("seed_all")

    async def _fake_seed_admin_user(session) -> None:
        calls.append("seed_admin_user")

    monkeypatch.setattr(seed_module, "seed_all", _fake_seed_all)
    monkeypatch.setattr(seed_module, "seed_admin_user", _fake_seed_admin_user)
    monkeypatch.setattr(seed_module, "AsyncSessionLocal", TestSessionLocal)

    await seed_module.main(admin_only=False)

    assert calls == ["seed_all", "seed_admin_user"]
