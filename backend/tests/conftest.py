import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  (registers all ORM models on Base's mapper registry)
from app.core.database import Base, get_db
from app.main import app
from app.models import Anime, Character, Faction, TemporalFact
from app.services import llm_synthesizer

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
        await session.flush()

        session.add(
            Character(anime_id=anime.id, name="Lelouch Lamperouge", faction_id=faction.id)
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
        await session.commit()


@pytest.fixture(scope="session", autouse=True)
def _prepare_database() -> Generator[None, None, None]:
    asyncio.run(_seed_fixture_data())
    yield


@pytest.fixture(autouse=True)
def _no_live_gemini_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the deterministic template path by default in every test.

    Tests must never depend on whether a real GEMINI_API_KEY happens to be present in
    the ambient environment — that would make the suite flaky and hit live network/API
    calls. Tests in test_rag.py that specifically exercise the LLM path re-patch
    llm_synthesizer.get_settings themselves, which simply overrides this default.
    """

    class _NoGeminiSettings:
        gemini_api_key = ""

    monkeypatch.setattr(llm_synthesizer, "get_settings", lambda: _NoGeminiSettings())


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
