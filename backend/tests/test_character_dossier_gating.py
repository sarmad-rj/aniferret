"""Tests for character-level spoiler gating: bounty/power/backstory must stay masked
until a character's own first_revealed_at checkpoint, while identity fields (name,
role, height, avatar) remain visible regardless (see app/services/dossier_service.py).
"""

from fastapi.testclient import TestClient


def _get_suzaku(client: TestClient, checkpoint: str) -> dict:
    response = client.get("/api/v1/dossier/code-geass", params={"checkpoint": checkpoint})
    assert response.status_code == 200
    body = response.json()
    return next(c for c in body["characters"] if c["name"] == "Suzaku Kururugi")


def test_character_deep_fields_masked_before_first_revealed_at(client: TestClient) -> None:
    suzaku = _get_suzaku(client, "S1E10")

    assert suzaku["is_revealed"] is False
    assert suzaku["bounty"] is None
    assert suzaku["power"] is None
    assert suzaku["backstory"] is None


def test_character_identity_fields_always_visible(client: TestClient) -> None:
    suzaku = _get_suzaku(client, "S1E10")

    assert suzaku["name"] == "Suzaku Kururugi"
    assert suzaku["role"] == "Knight"
    assert suzaku["height"] == "178 cm"
    assert suzaku["avatar_url"] == "https://example.com/suzaku.jpg"
    assert suzaku["first_revealed_at"] == "S1E12"


def test_character_deep_fields_unlock_at_first_revealed_at(client: TestClient) -> None:
    suzaku = _get_suzaku(client, "S1E12")

    assert suzaku["is_revealed"] is True
    assert suzaku["power"] == "Lancelot Frame Pilot"
    assert suzaku["backstory"] == "Secretly resents his father, the former Prime Minister of Japan."


def test_character_deep_fields_remain_unlocked_after_first_revealed_at(client: TestClient) -> None:
    suzaku = _get_suzaku(client, "S2E1")

    assert suzaku["is_revealed"] is True
    assert suzaku["power"] == "Lancelot Frame Pilot"
