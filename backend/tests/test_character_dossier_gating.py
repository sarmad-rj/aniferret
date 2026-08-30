"""Tests for character introduction gating: a character not yet introduced
(first_revealed_at > checkpoint) must be omitted from the dossier's character list
entirely, not merely field-masked (see app/services/dossier_service.py). Once
introduced, all of their dossier fields are fully populated — there is no separate
per-field spoiler lock layer.
"""

from fastapi.testclient import TestClient


def _get_character_names(client: TestClient, checkpoint: str) -> set[str]:
    response = client.get("/api/v1/dossier/code-geass", params={"checkpoint": checkpoint})
    assert response.status_code == 200
    return {c["name"] for c in response.json()["characters"]}


def _get_suzaku(client: TestClient, checkpoint: str) -> dict:
    response = client.get("/api/v1/dossier/code-geass", params={"checkpoint": checkpoint})
    assert response.status_code == 200
    body = response.json()
    return next(c for c in body["characters"] if c["name"] == "Suzaku Kururugi")


def test_unintroduced_character_is_omitted_before_first_revealed_at(client: TestClient) -> None:
    names = _get_character_names(client, "S1E10")

    assert "Suzaku Kururugi" not in names
    assert "Lelouch Lamperouge" in names  # first_revealed_at defaults to S1E1


def test_character_appears_and_is_fully_populated_at_first_revealed_at(client: TestClient) -> None:
    suzaku = _get_suzaku(client, "S1E12")

    assert suzaku["is_revealed"] is True
    assert suzaku["role"] == "Knight"
    assert suzaku["height"] == "178 cm"
    assert suzaku["avatar_url"] == "https://example.com/suzaku.jpg"
    assert suzaku["power"] == "Lancelot Frame Pilot"
    assert suzaku["backstory"] == "Secretly resents his father, the former Prime Minister of Japan."


def test_character_remains_visible_after_first_revealed_at(client: TestClient) -> None:
    names = _get_character_names(client, "S2E1")

    assert "Suzaku Kururugi" in names
