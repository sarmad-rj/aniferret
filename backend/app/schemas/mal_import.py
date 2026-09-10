from typing import Literal

from pydantic import BaseModel

from app.schemas.checkpoint import CheckpointStr


class MalImportedEntry(BaseModel):
    title: str
    anime_slug: str
    checkpoint: CheckpointStr
    mal_id: int | None


class MalSkippedEntry(BaseModel):
    """A matched entry whose checkpoint was deliberately not auto-set — always a
    multi-season franchise, where a single MAL entry's watched_episodes/status can't
    be mapped to the right season without guessing. See mal_import_service for why
    guessing wrong here is a spoiler-leak risk, not a cosmetic one.

    watched_episodes is carried through (not discarded) so the frontend's manual
    review page can pre-fill each show's slider from it as a starting point — never
    auto-submitted, the user still has to confirm via Save All, so this doesn't
    reopen the spoiler-safety question above, it just saves them scrubbing a
    hundreds-of-episodes-long slider from episode 1 every time."""

    title: str
    anime_slug: str
    mal_id: int | None
    watched_episodes: int
    reason: Literal["ambiguous_season_for_multi_season_franchise"]


class MalImportResponse(BaseModel):
    total_in_file: int
    matched_count: int
    no_progress_count: int
    """Matched, but nothing to sync — zero watched episodes and not marked Completed.
    Kept separate from `skipped` so that bucket only ever means "ambiguous," not
    "nothing happened." Invariant: matched_count == len(imported) + len(skipped) +
    no_progress_count, and total_in_file == matched_count + len(unmatched)."""
    imported: list[MalImportedEntry]
    skipped: list[MalSkippedEntry]
    unmatched: list[str]
