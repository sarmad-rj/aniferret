import httpx
from sqlalchemy import select

from app.models.anime import Anime
from app.models.anime_external_metadata import AnimeExternalMetadata
from app.services import ingestion_service
from tests.conftest import TestSessionLocal


class _FakeResponse:
    def __init__(self, json_data: dict, status_code: int = 200) -> None:
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)

    def json(self) -> dict:
        return self._json_data


class _FakeAsyncClient:
    def __init__(self, response: _FakeResponse | None = None, raise_error: bool = False) -> None:
        self._response = response
        self._raise_error = raise_error

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, *args) -> bool:
        return False

    async def get(self, url: str) -> _FakeResponse:
        if self._raise_error:
            raise httpx.ConnectError("simulated network failure")
        return self._response

    async def post(self, url: str, json: dict | None = None) -> _FakeResponse:
        if self._raise_error:
            raise httpx.ConnectError("simulated network failure")
        return self._response


async def test_fetch_jikan_metadata_success(monkeypatch) -> None:
    response = _FakeResponse(
        {"data": {"title": "Code Geass", "episodes": 25, "score": 8.7, "synopsis": "Lore."}}
    )
    monkeypatch.setattr(
        ingestion_service.httpx, "AsyncClient", lambda **kwargs: _FakeAsyncClient(response=response)
    )

    result = await ingestion_service.fetch_jikan_metadata(1575)

    assert result == {"title": "Code Geass", "episodes": 25, "score": 8.7, "synopsis": "Lore."}


async def test_fetch_jikan_metadata_network_failure_returns_none(monkeypatch) -> None:
    monkeypatch.setattr(
        ingestion_service.httpx, "AsyncClient", lambda **kwargs: _FakeAsyncClient(raise_error=True)
    )

    assert await ingestion_service.fetch_jikan_metadata(1575) is None


async def test_fetch_jikan_metadata_missing_data_returns_none(monkeypatch) -> None:
    response = _FakeResponse({"data": None})
    monkeypatch.setattr(
        ingestion_service.httpx, "AsyncClient", lambda **kwargs: _FakeAsyncClient(response=response)
    )

    assert await ingestion_service.fetch_jikan_metadata(999999) is None


async def test_fetch_anilist_metadata_success(monkeypatch) -> None:
    response = _FakeResponse(
        {
            "data": {
                "Media": {
                    "title": {"romaji": "Code Geass"},
                    "episodes": 25,
                    "averageScore": 85,
                    "description": "Lore.",
                }
            }
        }
    )
    monkeypatch.setattr(
        ingestion_service.httpx, "AsyncClient", lambda **kwargs: _FakeAsyncClient(response=response)
    )

    result = await ingestion_service.fetch_anilist_metadata(1575)

    assert result == {"title": "Code Geass", "episodes": 25, "score": 8.5, "synopsis": "Lore."}


async def test_fetch_anilist_metadata_missing_media_returns_none(monkeypatch) -> None:
    response = _FakeResponse({"data": {"Media": None}})
    monkeypatch.setattr(
        ingestion_service.httpx, "AsyncClient", lambda **kwargs: _FakeAsyncClient(response=response)
    )

    assert await ingestion_service.fetch_anilist_metadata(999999) is None


async def test_fetch_anilist_metadata_network_failure_returns_none(monkeypatch) -> None:
    monkeypatch.setattr(
        ingestion_service.httpx, "AsyncClient", lambda **kwargs: _FakeAsyncClient(raise_error=True)
    )

    assert await ingestion_service.fetch_anilist_metadata(1575) is None


def test_detect_conflicts_flags_episode_and_title_mismatch() -> None:
    anime = Anime(
        id=1, slug="code-geass", title="Code Geass", total_episodes=50, season_episode_counts=[25, 25]
    )
    records = [
        AnimeExternalMetadata(
            anime_id=1, source="jikan", title="Code Geass: Hangyaku no Lelouch", episodes=25
        ),
        AnimeExternalMetadata(
            anime_id=1, source="anilist", title="Code Geass: Hangyaku no Lelouch", episodes=25
        ),
    ]

    conflicts = ingestion_service.detect_conflicts(anime, records)

    fields = {conflict["field"] for conflict in conflicts}
    assert fields == {"episodes", "title"}
    episode_conflict = next(c for c in conflicts if c["field"] == "episodes")
    assert episode_conflict["values"] == {"aniferret": 50, "jikan": 25, "anilist": 25}


def test_detect_conflicts_no_conflict_when_values_agree() -> None:
    anime = Anime(
        id=1,
        slug="attack-on-titan",
        title="Shingeki no Kyojin",
        total_episodes=25,
        season_episode_counts=[25],
    )
    records = [
        AnimeExternalMetadata(anime_id=1, source="jikan", title="Shingeki no Kyojin", episodes=25),
    ]

    assert ingestion_service.detect_conflicts(anime, records) == []


def test_detect_conflicts_ignores_records_with_no_episode_value() -> None:
    anime = Anime(
        id=1, slug="code-geass", title="Code Geass", total_episodes=50, season_episode_counts=[25, 25]
    )
    records = [AnimeExternalMetadata(anime_id=1, source="jikan", title="Code Geass", episodes=None)]

    conflicts = ingestion_service.detect_conflicts(anime, records)

    assert all(conflict["field"] != "episodes" for conflict in conflicts)


async def test_sources_endpoint_returns_records_and_conflicts(client) -> None:
    async with TestSessionLocal() as session:
        result = await session.execute(select(Anime).where(Anime.slug == "code-geass"))
        anime = result.scalar_one()
        session.add(
            AnimeExternalMetadata(
                anime_id=anime.id, source="jikan", title="Code Geass: Hangyaku no Lelouch", episodes=25
            )
        )
        await session.commit()

    response = client.get("/api/v1/anime/code-geass/sources")

    assert response.status_code == 200
    body = response.json()
    sources_present = {record["source"] for record in body["records"]}
    assert sources_present == {"aniferret", "jikan"}
    fields = {conflict["field"] for conflict in body["conflicts"]}
    assert "episodes" in fields  # curated total_episodes=50 vs jikan's 25


def test_sources_endpoint_unknown_anime_returns_404(client) -> None:
    response = client.get("/api/v1/anime/no-such-anime/sources")

    assert response.status_code == 404
