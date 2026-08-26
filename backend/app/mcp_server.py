"""Standalone MCP server exposing AniFerret's progress-gated dossier tools (SPEC.md D5).

Run directly (stdio transport, the MCP default): python app/mcp_server.py
Registered in .claude/mcp.json under "aniferret-dossiers".
"""

import sys
from pathlib import Path

# Runnable directly as a script (not via `python -m`), so backend/ must be on sys.path
# before any `app.*` import below can resolve.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app import models  # noqa: E402, F401  (registers all ORM models on Base's mapper registry)
from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.temporal_fact import TemporalFact  # noqa: E402
from app.services.dossier_service import AnimeNotFoundError, get_anime_by_slug  # noqa: E402
from app.services.reveal_engine import (  # noqa: E402
    InvalidCheckpointError,
    filter_visible_facts,
    is_revealed,
)

try:
    from mcp.server.fastmcp import FastMCP  # mcp<2.0
except ModuleNotFoundError:
    from mcp.server.mcpserver import MCPServer as FastMCP  # "FastMCP" renamed to MCPServer in mcp>=2.0

mcp = FastMCP("aniferret-dossiers")


@mcp.tool()
async def get_faction_hierarchy(anime_slug: str, checkpoint: str) -> dict:
    """Return the progress-gated faction hierarchy (factions + member rosters) for an anime."""
    async with AsyncSessionLocal() as session:
        try:
            anime = await get_anime_by_slug(session, anime_slug)
        except AnimeNotFoundError as exc:
            return {"error": str(exc)}

        try:
            visible_facts = filter_visible_facts(anime.facts, checkpoint)
        except InvalidCheckpointError as exc:
            return {"error": str(exc)}

        factions = []
        for faction in anime.factions:
            members = [c.name for c in anime.characters if c.faction_id == faction.id]
            factions.append(
                {
                    "faction": faction.name,
                    "description": faction.description,
                    "members": members,
                    "revealed_fact_count": sum(
                        1 for fact in visible_facts if fact.subject == faction.name
                    ),
                }
            )

        return {"anime_slug": anime_slug, "checkpoint": checkpoint, "factions": factions}


@mcp.tool()
async def get_character_dossier(anime_slug: str, character_name: str, checkpoint: str) -> dict:
    """Return a single character's progress-gated dossier (revealed facts only)."""
    async with AsyncSessionLocal() as session:
        try:
            anime = await get_anime_by_slug(session, anime_slug)
        except AnimeNotFoundError as exc:
            return {"error": str(exc)}

        character = next(
            (c for c in anime.characters if c.name.lower() == character_name.lower()), None
        )
        if character is None:
            return {"error": f"No character named {character_name!r} found in {anime_slug!r}"}

        try:
            visible_facts = filter_visible_facts(anime.facts, checkpoint)
        except InvalidCheckpointError as exc:
            return {"error": str(exc)}

        revealed = [
            {
                "predicate": fact.predicate,
                "object": fact.object,
                "source_citation": fact.source_citation,
            }
            for fact in visible_facts
            if fact.subject == character.name
        ]

        return {
            "anime_slug": anime_slug,
            "checkpoint": checkpoint,
            "character": character.name,
            "faction_id": character.faction_id,
            "revealed_facts": revealed,
        }


@mcp.tool()
async def evaluate_reveal_status(fact_id: int, checkpoint: str) -> dict:
    """Check whether a fact is revealed at a checkpoint. Fact content is included only if revealed."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TemporalFact).where(TemporalFact.fact_id == fact_id)
        )
        fact = result.scalar_one_or_none()
        if fact is None:
            return {"error": f"No fact found with fact_id={fact_id}"}

        try:
            revealed = is_revealed(fact.first_revealed_at, checkpoint)
        except InvalidCheckpointError as exc:
            return {"error": str(exc)}

        if not revealed:
            return {"fact_id": fact_id, "checkpoint": checkpoint, "is_revealed": False}

        return {
            "fact_id": fact_id,
            "checkpoint": checkpoint,
            "is_revealed": True,
            "subject": fact.subject,
            "predicate": fact.predicate,
            "object": fact.object,
            "source_citation": fact.source_citation,
        }


if __name__ == "__main__":
    mcp.run()
