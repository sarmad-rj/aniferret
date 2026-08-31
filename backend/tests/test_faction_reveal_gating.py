"""Tests for faction-container visibility gating (app/services/dossier_service.py's
_prune_empty_factions): a faction with its own `first_revealed_at` renders as soon as
that checkpoint is reached, even with zero introduced members — for structural lore
(e.g. a class-ranking system, an empire) that's public knowledge independent of any one
member's debut. A faction with no `first_revealed_at` keeps the legacy member-only gate.
"""

from fastapi.testclient import TestClient


def _get_faction_names(client: TestClient, checkpoint: str) -> set[str]:
    response = client.get("/api/v1/dossier/code-geass", params={"checkpoint": checkpoint})
    assert response.status_code == 200
    return {f["name"] for f in response.json()["factions"]}


def test_structural_faction_visible_before_any_member_is_revealed(client: TestClient) -> None:
    names = _get_faction_names(client, "S1E1")

    assert "Holy Britannian Empire" in names


def test_structural_faction_hidden_before_its_own_checkpoint(client: TestClient) -> None:
    names = _get_faction_names(client, "S1E10")

    assert "Chinese Federation" not in names


def test_structural_faction_visible_once_its_own_checkpoint_is_reached(
    client: TestClient,
) -> None:
    names = _get_faction_names(client, "S1E20")

    assert "Chinese Federation" in names


def test_member_gated_faction_visible_once_its_member_debuts(client: TestClient) -> None:
    """Legacy behavior for a faction with no first_revealed_at: Black Knights has no
    structural reveal checkpoint of its own, so it's gated purely by its member
    Lelouch (fixture: Black Knights member from S1E1)."""
    names = _get_faction_names(client, "S1E1")

    assert "Black Knights" in names
