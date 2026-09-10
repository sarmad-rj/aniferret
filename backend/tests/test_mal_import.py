"""Tests for MyAnimeList XML/gzip watch-progress import — see
app/services/mal_import_service.py for the matching/checkpoint-safety algorithm this
exercises. The most safety-critical case is multi-season franchises: a single MAL
entry's status/watched_episodes can't be mapped to the right season without guessing,
and guessing wrong is a spoiler leak (see that module's docstring), so those must
always land in `skipped`, never auto-set a checkpoint, regardless of MAL status.
"""

import asyncio
import gzip

from fastapi.testclient import TestClient

from app.models.anime import Anime
from app.services.mal_import_service import MAX_UPLOAD_SIZE_BYTES
from tests.conftest import TestSessionLocal, _mark_verified


def _register(client: TestClient, email: str, password: str = "password123") -> str:
    response = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201
    asyncio.run(_mark_verified(email))

    login_response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


async def _create_anime(**kwargs) -> None:
    async with TestSessionLocal() as session:
        session.add(Anime(**kwargs))
        await session.commit()


def _mal_export_xml(entries: list[dict]) -> bytes:
    anime_nodes = "".join(
        f"""
        <anime>
          <series_animedb_id>{entry.get("mal_id", "")}</series_animedb_id>
          <series_title><![CDATA[{entry.get("title", "")}]]></series_title>
          <my_watched_episodes>{entry.get("watched_episodes", 0)}</my_watched_episodes>
          <my_status>{entry.get("status", "Watching")}</my_status>
        </anime>
        """
        for entry in entries
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<myanimelist>
  <myinfo></myinfo>
  {anime_nodes}
</myanimelist>"""
    return xml.encode("utf-8")


def _upload(client: TestClient, token: str, content: bytes, filename: str = "export.xml"):
    return client.post(
        "/api/v1/me/watch-progress/import-mal",
        files={"file": (filename, content, "text/xml")},
        headers={"Authorization": f"Bearer {token}"},
    )


def test_import_valid_single_season_xml_sets_checkpoint(client: TestClient) -> None:
    asyncio.run(
        _create_anime(
            slug="mal-import-single",
            title="Single Season Anime",
            total_episodes=24,
            mal_id=1001,
            season_episode_counts=[24],
        )
    )
    token = _register(client, "mal-single@example.com")

    xml = _mal_export_xml(
        [{"mal_id": 1001, "title": "Single Season Anime", "watched_episodes": 10, "status": "Watching"}]
    )
    response = _upload(client, token, xml)

    assert response.status_code == 200
    body = response.json()
    assert body["total_in_file"] == 1
    assert body["matched_count"] == 1
    assert body["imported"] == [
        {"title": "Single Season Anime", "anime_slug": "mal-import-single", "checkpoint": "S1E10", "mal_id": 1001}
    ]
    assert body["skipped"] == []
    assert body["unmatched"] == []

    progress = client.get(
        "/api/v1/me/watch-progress", headers={"Authorization": f"Bearer {token}"}
    ).json()
    assert {"anime_slug": "mal-import-single", "checkpoint": "S1E10"} in progress["entries"]


def test_import_single_season_completed_sets_final_checkpoint(client: TestClient) -> None:
    asyncio.run(
        _create_anime(
            slug="mal-import-single-completed",
            title="Single Season Completed",
            total_episodes=24,
            mal_id=1002,
            season_episode_counts=[24],
        )
    )
    token = _register(client, "mal-single-completed@example.com")

    # watched_episodes intentionally omitted/zero -- some MAL clients don't fill it
    # in for Completed entries; status alone must be enough to resolve the finale.
    xml = _mal_export_xml(
        [{"mal_id": 1002, "title": "Single Season Completed", "watched_episodes": 0, "status": "Completed"}]
    )
    body = _upload(client, token, xml).json()

    assert body["imported"][0]["checkpoint"] == "S1E24"


def test_import_rejects_corrupted_gzip_data(client: TestClient) -> None:
    token = _register(client, "mal-corrupt-gzip@example.com")

    # Valid gzip magic bytes, garbage after -- distinct from the plain "not gzip at
    # all" case, exercises the decompression-failure path specifically.
    corrupted = b"\x1f\x8b" + b"not actually valid gzip content"
    response = _upload(client, token, corrupted, filename="export.xml.gz")

    assert response.status_code == 400


def test_import_multi_season_never_auto_sets_regardless_of_status(client: TestClient) -> None:
    asyncio.run(
        _create_anime(
            slug="mal-import-multi-completed",
            title="Multi Season Completed",
            total_episodes=44,
            mal_id=2001,
            season_episode_counts=[25, 19],
        )
    )
    asyncio.run(
        _create_anime(
            slug="mal-import-multi-partial",
            title="Multi Season Partial",
            total_episodes=36,
            mal_id=2002,
            season_episode_counts=[12, 12, 12],
        )
    )
    token = _register(client, "mal-multi@example.com")

    xml = _mal_export_xml(
        [
            {"mal_id": 2001, "title": "Multi Season Completed", "watched_episodes": 25, "status": "Completed"},
            {"mal_id": 2002, "title": "Multi Season Partial", "watched_episodes": 5, "status": "Watching"},
        ]
    )
    response = _upload(client, token, xml)

    assert response.status_code == 200
    body = response.json()
    assert body["imported"] == []
    assert {entry["anime_slug"] for entry in body["skipped"]} == {
        "mal-import-multi-completed",
        "mal-import-multi-partial",
    }
    assert all(
        entry["reason"] == "ambiguous_season_for_multi_season_franchise" for entry in body["skipped"]
    )
    watched_by_slug = {entry["anime_slug"]: entry["watched_episodes"] for entry in body["skipped"]}
    assert watched_by_slug == {
        "mal-import-multi-completed": 25,
        "mal-import-multi-partial": 5,
    }

    progress = client.get(
        "/api/v1/me/watch-progress", headers={"Authorization": f"Bearer {token}"}
    ).json()
    assert progress["entries"] == []


def test_import_matched_zero_progress_entry_is_excluded_not_skipped(client: TestClient) -> None:
    asyncio.run(
        _create_anime(
            slug="mal-import-zero-progress",
            title="Zero Progress Anime",
            total_episodes=24,
            mal_id=3001,
            season_episode_counts=[12, 12],
        )
    )
    token = _register(client, "mal-zero-progress@example.com")

    xml = _mal_export_xml(
        [{"mal_id": 3001, "title": "Zero Progress Anime", "watched_episodes": 0, "status": "Plan to Watch"}]
    )
    body = _upload(client, token, xml).json()

    assert body["matched_count"] == 1
    assert body["no_progress_count"] == 1
    assert body["imported"] == []
    assert body["skipped"] == []
    assert body["unmatched"] == []


def test_import_matches_by_mal_id(client: TestClient) -> None:
    asyncio.run(
        _create_anime(
            slug="totally-different-slug",
            title="A Title That Would Never Slug Match",
            total_episodes=12,
            mal_id=4001,
            season_episode_counts=[12],
        )
    )
    token = _register(client, "mal-id-match@example.com")

    xml = _mal_export_xml(
        [{"mal_id": 4001, "title": "Some Completely Different MAL Title", "watched_episodes": 5, "status": "Watching"}]
    )
    body = _upload(client, token, xml).json()

    assert body["imported"][0]["anime_slug"] == "totally-different-slug"
    assert body["imported"][0]["checkpoint"] == "S1E5"


def test_import_falls_back_to_slug_match(client: TestClient) -> None:
    asyncio.run(
        _create_anime(
            slug="fallback-match-anime",
            title="Fallback Match Anime",
            total_episodes=12,
            mal_id=None,
            season_episode_counts=[12],
        )
    )
    token = _register(client, "mal-slug-fallback@example.com")

    xml = _mal_export_xml(
        [{"mal_id": 9999, "title": "Fallback Match Anime", "watched_episodes": 3, "status": "Watching"}]
    )
    body = _upload(client, token, xml).json()

    assert body["imported"][0]["anime_slug"] == "fallback-match-anime"
    assert body["imported"][0]["checkpoint"] == "S1E3"


def test_import_reports_unmatched_titles(client: TestClient) -> None:
    token = _register(client, "mal-unmatched@example.com")

    xml = _mal_export_xml(
        [{"mal_id": 8888, "title": "Totally Unknown Anime XYZ", "watched_episodes": 5, "status": "Watching"}]
    )
    body = _upload(client, token, xml).json()

    assert body["matched_count"] == 0
    assert body["unmatched"] == ["Totally Unknown Anime XYZ"]
    assert body["imported"] == []


def test_import_rejects_invalid_file_extension(client: TestClient) -> None:
    token = _register(client, "mal-bad-ext@example.com")

    response = _upload(client, token, b"not xml", filename="export.txt")

    assert response.status_code == 400


def test_import_rejects_malformed_xml(client: TestClient) -> None:
    token = _register(client, "mal-malformed@example.com")

    response = _upload(client, token, b"this is < not valid xml")

    assert response.status_code == 400


def test_import_rejects_entity_expansion_xml(client: TestClient) -> None:
    token = _register(client, "mal-entity-bomb@example.com")

    malicious = (
        b'<?xml version="1.0"?>'
        b"<!DOCTYPE myanimelist [<!ENTITY lol \"lol\"><!ENTITY lol2 \"&lol;&lol;&lol;&lol;&lol;\">]>"
        b"<myanimelist><anime><series_title>&lol2;</series_title></anime></myanimelist>"
    )

    response = _upload(client, token, malicious)

    assert response.status_code == 400


def test_import_accepts_gzip_and_plain_xml_identically(client: TestClient) -> None:
    asyncio.run(
        _create_anime(
            slug="gzip-parity-anime",
            title="Gzip Parity Anime",
            total_episodes=12,
            mal_id=5555,
            season_episode_counts=[12],
        )
    )
    entries = [{"mal_id": 5555, "title": "Gzip Parity Anime", "watched_episodes": 6, "status": "Watching"}]
    xml = _mal_export_xml(entries)

    token_plain = _register(client, "mal-gzip-plain@example.com")
    plain_body = _upload(client, token_plain, xml, filename="export.xml").json()

    token_gz = _register(client, "mal-gzip-compressed@example.com")
    gz_body = _upload(client, token_gz, gzip.compress(xml), filename="export.xml.gz").json()

    for key in ("total_in_file", "matched_count", "no_progress_count", "imported", "skipped", "unmatched"):
        assert plain_body[key] == gz_body[key]


def test_import_rejects_oversized_upload(client: TestClient) -> None:
    token = _register(client, "mal-oversized@example.com")

    oversized = b"<a>" + b"a" * (MAX_UPLOAD_SIZE_BYTES + 1) + b"</a>"
    response = _upload(client, token, oversized)

    assert response.status_code == 400


def test_import_rejects_gzip_bomb_exceeding_decompressed_cap(client: TestClient) -> None:
    token = _register(client, "mal-gzip-bomb@example.com")

    # Highly repetitive -> compresses to a tiny payload but decompresses well past
    # the 50 MB cap; proves the streamed-decompression abort fires before the full
    # bomb is ever materialized (this test itself completing quickly is part of
    # what it's proving).
    bomb = gzip.compress(b"a" * (60 * 1024 * 1024))
    response = _upload(client, token, bomb, filename="export.xml.gz")

    assert response.status_code == 400


def test_import_rejects_unauthenticated_request(client: TestClient) -> None:
    response = client.post(
        "/api/v1/me/watch-progress/import-mal",
        files={"file": ("export.xml", _mal_export_xml([]), "text/xml")},
    )

    assert response.status_code == 401


def test_import_dedupes_entries_mapping_to_same_anime_keeping_highest_progress(
    client: TestClient,
) -> None:
    asyncio.run(
        _create_anime(
            slug="dedupe-anime",
            title="Dedupe Anime",
            total_episodes=24,
            mal_id=None,
            season_episode_counts=[24],
        )
    )
    token = _register(client, "mal-dedupe@example.com")

    xml = _mal_export_xml(
        [
            {"mal_id": 111, "title": "Dedupe Anime", "watched_episodes": 5, "status": "Watching"},
            {"mal_id": 222, "title": "Dedupe Anime", "watched_episodes": 15, "status": "Watching"},
        ]
    )
    body = _upload(client, token, xml).json()

    matching = [entry for entry in body["imported"] if entry["anime_slug"] == "dedupe-anime"]
    assert len(matching) == 1
    assert matching[0]["checkpoint"] == "S1E15"

    progress = client.get(
        "/api/v1/me/watch-progress", headers={"Authorization": f"Bearer {token}"}
    ).json()
    dedupe_entries = [e for e in progress["entries"] if e["anime_slug"] == "dedupe-anime"]
    assert len(dedupe_entries) == 1
    assert dedupe_entries[0]["checkpoint"] == "S1E15"


def test_import_clamps_watched_episodes_exceeding_known_total(client: TestClient) -> None:
    asyncio.run(
        _create_anime(
            slug="clamp-anime",
            title="Clamp Anime",
            total_episodes=12,
            mal_id=5001,
            season_episode_counts=[12],
        )
    )
    token = _register(client, "mal-clamp@example.com")

    xml = _mal_export_xml(
        [{"mal_id": 5001, "title": "Clamp Anime", "watched_episodes": 999, "status": "Watching"}]
    )
    body = _upload(client, token, xml).json()

    assert body["imported"][0]["checkpoint"] == "S1E12"


def test_import_empty_anime_list_returns_zeroed_summary(client: TestClient) -> None:
    token = _register(client, "mal-empty@example.com")

    response = _upload(client, token, _mal_export_xml([]))

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "total_in_file": 0,
        "matched_count": 0,
        "no_progress_count": 0,
        "imported": [],
        "skipped": [],
        "unmatched": [],
    }


def test_import_upserts_rather_than_duplicating(client: TestClient) -> None:
    asyncio.run(
        _create_anime(
            slug="mal-upsert-anime",
            title="Upsert Anime",
            total_episodes=24,
            mal_id=6001,
            season_episode_counts=[24],
        )
    )
    token = _register(client, "mal-upsert@example.com")

    _upload(
        client, token,
        _mal_export_xml([{"mal_id": 6001, "title": "Upsert Anime", "watched_episodes": 5, "status": "Watching"}]),
    )
    _upload(
        client, token,
        _mal_export_xml([{"mal_id": 6001, "title": "Upsert Anime", "watched_episodes": 20, "status": "Watching"}]),
    )

    progress = client.get(
        "/api/v1/me/watch-progress", headers={"Authorization": f"Bearer {token}"}
    ).json()
    upsert_entries = [e for e in progress["entries"] if e["anime_slug"] == "mal-upsert-anime"]
    assert len(upsert_entries) == 1
    assert upsert_entries[0]["checkpoint"] == "S1E20"
