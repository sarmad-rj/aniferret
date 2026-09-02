import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  (registers all ORM models on Base's mapper registry)
from app.core.database import Base, get_db
from app.main import app
from app.models import Anime, Character, Faction, Franchise, FranchiseEntry, TemporalFact
from app.services import ingestion_service, llm_synthesizer

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


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session")
def auth_token() -> str:
    """A valid bearer token for one shared test user, registered once per test
    session — for tests that need *some* authenticated identity (e.g. Group Mode
    gating) without caring which one. Tests exercising register/login itself use
    their own distinct emails instead, via the `client` fixture directly."""
    with TestClient(app) as session_client:
        response = session_client.post(
            "/api/v1/auth/register",
            json={"email": "fixture-user@example.com", "password": "password123"},
        )
        assert response.status_code == 201
        return response.json()["access_token"]
