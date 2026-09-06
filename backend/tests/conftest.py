import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  (registers all ORM models on Base's mapper registry)
from app.core.database import Base, get_db
from app.main import app
from app.models import Anime, Character, Faction, Franchise, FranchiseEntry, TemporalFact, User
from app.services import email_service, ingestion_service, llm_synthesizer

test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False, class_=AsyncSession)


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


async def _seed_fixture_data() -> None:
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        anime = Anime(slug="code-geass", title="Code Geass", total_episodes=50)
        session.add(anime)
        await session.flush()

        faction = Faction(anime_id=anime.id, name="Black Knights", description="Resistance force.")
        session.add(faction)
        session.add(
            Faction(
                anime_id=anime.id,
                name="Holy Britannian Empire",
                description="The ruling imperial power.",
                first_revealed_at="S1E1",
            )
        )
        session.add(
            Faction(
                anime_id=anime.id,
                name="Chinese Federation",
                description="A rival superpower revealed later in the story.",
                first_revealed_at="S1E20",
            )
        )
        await session.flush()

        session.add(
            Character(anime_id=anime.id, name="Lelouch Lamperouge", faction_id=faction.id)
        )
        session.add(
            Character(
                anime_id=anime.id,
                name="Suzaku Kururugi",
                faction_id=None,
                role="Knight",
                height="178 cm",
                avatar_url="https://example.com/suzaku.jpg",
                power="Lancelot Frame Pilot",
                backstory="Secretly resents his father, the former Prime Minister of Japan.",
                first_revealed_at="S1E12",
            )
        )

        session.add_all(
            [
                TemporalFact(
                    anime_id=anime.id,
                    subject="Lelouch Lamperouge",
                    predicate="royal_lineage",
                    object="11th prince of the Holy Britannian Empire.",
                    source_citation="Season 1, Episode 1",
                    first_revealed_at="S1E1",
                    first_hinted_at=None,
                    confidence=0.99,
                ),
                TemporalFact(
                    anime_id=anime.id,
                    subject="Lelouch Lamperouge",
                    predicate="true_identity",
                    object="Zero, masked leader of the Black Knights.",
                    source_citation="Season 1, Episode 12",
                    first_revealed_at="S1E12",
                    first_hinted_at="S1E3",
                    confidence=0.97,
                ),
            ]
        )

        franchise = Franchise(slug="code-geass", name="Code Geass")
        session.add(franchise)
        await session.flush()

        session.add_all(
            [
                FranchiseEntry(
                    franchise_id=franchise.id,
                    anime_id=anime.id,
                    title="Code Geass: Lelouch of the Rebellion",
                    entry_type="tv",
                    release_order=1,
                    chronological_order=2,
                ),
                FranchiseEntry(
                    franchise_id=franchise.id,
                    anime_id=None,
                    title="Code Geass: Akito the Exiled (OVA)",
                    entry_type="ova",
                    release_order=2,
                    chronological_order=1,
                    note="A side-story OVA set chronologically before the TV series' Second Season.",
                ),
            ]
        )
        await session.commit()


@pytest.fixture(scope="session", autouse=True)
def _prepare_database() -> Generator[None, None, None]:
    asyncio.run(_seed_fixture_data())
    yield


@pytest.fixture(autouse=True)
def _no_live_gemini_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the deterministic/no-op path by default in every test.

    Tests must never depend on whether a real GEMINI_API_KEY happens to be present in
    the ambient environment — that would make the suite flaky and hit live network/API
    calls. llm_synthesizer and ingestion_service each import get_settings into their own
    module namespace, so both need patching independently. Tests that specifically
    exercise a live-key code path re-patch get_settings themselves, which simply
    overrides this default.
    """

    class _NoGeminiSettings:
        gemini_api_key = ""

    monkeypatch.setattr(llm_synthesizer, "get_settings", lambda: _NoGeminiSettings())
    monkeypatch.setattr(ingestion_service, "get_settings", lambda: _NoGeminiSettings())


@pytest.fixture(autouse=True)
def _no_live_smtp_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the deterministic/no-op path by default in every test, regardless of
    whether real SMTP credentials happen to be present in the ambient .env.

    This assumption used to just be true by circumstance (no real SMTP creds were
    ever configured) rather than being enforced — once real Gmail credentials were
    added to .env earlier in this project's life, every test that calls
    /auth/register, /auth/forgot-password, or /auth/resend-verification started
    silently attempting real SMTP connections to Gmail on every single call. This
    went unnoticed because email_service._send_email fails silently by design
    (logged, not raised) — it only surfaced as a flaky test once a slow/failed
    real connection attempt collided with test_rate_limiting.py's timing.

    Almost certainly a real contributor to live SMTP delivery problems too: this
    suite calls those endpoints dozens of times per run, and has been run many
    times this session -- hundreds of rapid, automated connection attempts to one
    Gmail account is exactly the kind of pattern Google's abuse detection flags.
    """

    class _NoSmtpSettings:
        smtp_host = ""
        smtp_port = 587
        smtp_user = ""
        smtp_password = ""
        emails_from = ""
        app_name = "AniFerret"
        frontend_url = "http://localhost:5173"

    monkeypatch.setattr(email_service, "get_settings", lambda: _NoSmtpSettings())


@pytest.fixture(autouse=True)
def _disable_rate_limiting() -> Generator[None, None, None]:
    """Auth endpoints are rate-limited per client IP; TestClient requests all share
    one address, and this suite calls /auth/register and /auth/login far more than
    any real limit allows. The one test exercising the limiter itself re-enables it
    locally and restores this after.

    Setting enabled=False only skips *raising* on an over-limit request — the
    underlying counter still increments on every call regardless (confirmed: the
    dedicated rate-limit tests passed in isolation but failed once the rest of the
    suite's few hundred register/login calls had already run first). Resetting the
    storage here, before every test, is what actually keeps counts from building up
    across the whole session.
    """
    from app.core.rate_limit import limiter

    limiter.enabled = False
    limiter.reset()
    yield
    limiter.enabled = False


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


async def _mark_verified(email: str) -> None:
    """Registration no longer auto-verifies (see test_email_auth.py for that flow
    itself) — fixtures that just need *some* logged-in identity bypass the email
    step directly at the DB layer rather than fishing the token out of a
    BackgroundTask."""
    async with TestSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        user.is_verified = True
        await session.commit()


@pytest.fixture(scope="session")
def auth_token() -> str:
    """A valid bearer token for one shared test user, registered once per test
    session — for tests that need *some* authenticated identity (e.g. Group Mode
    gating) without caring which one. Tests exercising register/login itself use
    their own distinct emails instead, via the `client` fixture directly."""
    with TestClient(app) as session_client:
        register_response = session_client.post(
            "/api/v1/auth/register",
            json={"email": "fixture-user@example.com", "password": "password123"},
        )
        assert register_response.status_code == 201
        asyncio.run(_mark_verified("fixture-user@example.com"))

        login_response = session_client.post(
            "/api/v1/auth/login",
            json={"email": "fixture-user@example.com", "password": "password123"},
        )
        assert login_response.status_code == 200
        return login_response.json()["access_token"]


async def _mark_admin(email: str) -> None:
    async with TestSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        user.is_admin = True
        await session.commit()


@pytest.fixture(scope="session")
def admin_auth_token() -> str:
    """A valid bearer token for one shared admin test user — for tests that need an
    admin-gated identity (e.g. the anime-import endpoint, /admin/*) without caring
    which admin. test_admin.py's own tests use their own distinct emails to exercise
    admin-vs-non-admin gating itself."""
    with TestClient(app) as session_client:
        register_response = session_client.post(
            "/api/v1/auth/register",
            json={"email": "fixture-admin@example.com", "password": "password123"},
        )
        assert register_response.status_code == 201
        asyncio.run(_mark_verified("fixture-admin@example.com"))
        asyncio.run(_mark_admin("fixture-admin@example.com"))

        login_response = session_client.post(
            "/api/v1/auth/login",
            json={"email": "fixture-admin@example.com", "password": "password123"},
        )
        assert login_response.status_code == 200
        return login_response.json()["access_token"]
