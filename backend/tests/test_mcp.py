import pytest

from app import mcp_server
from tests.conftest import TestSessionLocal


@pytest.fixture(autouse=True)
def _use_test_session(monkeypatch):
    """Point the MCP server's session factory at the same in-memory fixture DB as the rest of the suite."""
    monkeypatch.setattr(mcp_server, "AsyncSessionLocal", TestSessionLocal)


async def test_get_faction_hierarchy_returns_gated_factions() -> None:
    result = await mcp_server.get_faction_hierarchy("code-geass", "S1E1")

    assert result["anime_slug"] == "code-geass"
    faction_names = {faction["faction"] for faction in result["factions"]}
    assert "Black Knights" in faction_names
    black_knights = next(f for f in result["factions"] if f["faction"] == "Black Knights")
    assert "Lelouch Lamperouge" in black_knights["members"]


async def test_get_faction_hierarchy_unknown_anime_returns_error() -> None:
    result = await mcp_server.get_faction_hierarchy("no-such-anime", "S1E1")
    assert "error" in result


async def test_get_character_dossier_hides_fact_before_checkpoint() -> None:
    result = await mcp_server.get_character_dossier("code-geass", "Lelouch Lamperouge", "S1E10")

    predicates = {fact["predicate"] for fact in result["revealed_facts"]}
    assert "true_identity" not in predicates
    assert "royal_lineage" in predicates


async def test_get_character_dossier_reveals_fact_at_checkpoint() -> None:
    result = await mcp_server.get_character_dossier("code-geass", "Lelouch Lamperouge", "S1E12")

    predicates = {fact["predicate"] for fact in result["revealed_facts"]}
    assert "true_identity" in predicates


async def test_get_character_dossier_unknown_character_returns_error() -> None:
    result = await mcp_server.get_character_dossier("code-geass", "Nobody", "S1E12")
    assert "error" in result


async def test_evaluate_reveal_status_locked_omits_content() -> None:
    # fact_id=2 is the Lelouch true_identity fact seeded in conftest.py, first_revealed_at=S1E12
    result = await mcp_server.evaluate_reveal_status(2, "S1E1")

    assert result["is_revealed"] is False
    assert "object" not in result


async def test_evaluate_reveal_status_revealed_includes_content() -> None:
    result = await mcp_server.evaluate_reveal_status(2, "S1E12")

    assert result["is_revealed"] is True
    assert result["object"] == "Zero, masked leader of the Black Knights."


async def test_evaluate_reveal_status_unknown_fact_returns_error() -> None:
    result = await mcp_server.evaluate_reveal_status(99999, "S1E1")
    assert "error" in result
