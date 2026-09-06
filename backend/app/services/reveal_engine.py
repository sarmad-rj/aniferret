import re
from collections.abc import Iterable

from app.models.temporal_fact import TemporalFact

_CHECKPOINT_RE = re.compile(r"^S(\d+)E(\d+)$", re.IGNORECASE)


class InvalidCheckpointError(ValueError):
    """Raised when a checkpoint string does not match the 'S<season>E<episode>' format."""


def parse_checkpoint(checkpoint: str) -> tuple[int, int]:
    """Parse 'S1E12' into a (season, episode) tuple that sorts correctly.

    Plain string comparison of checkpoints is wrong ('S1E12' < 'S1E9' lexicographically),
    so all gating logic must compare through this parsed tuple form instead.
    """
    match = _CHECKPOINT_RE.match(checkpoint.strip())
    if not match:
        raise InvalidCheckpointError(
            f"Invalid checkpoint format: {checkpoint!r}. Expected 'S<season>E<episode>', e.g. 'S1E12'."
        )
    return int(match.group(1)), int(match.group(2))


def is_revealed(first_revealed_at: str, user_checkpoint: str) -> bool:
    """Evaluate first_revealed_at <= user_checkpoint per SPEC.md Section 4.2."""
    return parse_checkpoint(first_revealed_at) <= parse_checkpoint(user_checkpoint)


def checkpoint_to_ordinal(checkpoint: str) -> int:
    """Flatten a checkpoint into a single sortable integer (season * 1000 + episode).

    ChromaDB metadata filters only support numeric comparison operators ($lte), not
    tuple comparison, so vector-store pre-filtering needs this scalar encoding rather
    than the raw 'S1E12' string. 1000 safely exceeds any real season's episode count.
    """
    season, episode = parse_checkpoint(checkpoint)
    return season * 1000 + episode


def checkpoint_to_absolute_episode(checkpoint: str, season_episode_counts: list[int]) -> int:
    """Convert a checkpoint into its 1-indexed absolute position across the full
    series, e.g. 'S2E5' with season_episode_counts=[12, 13] -> 12 + 5 = 17.

    Distinct from checkpoint_to_ordinal: that one is a ChromaDB-friendly sortable
    encoding (season * 1000 + episode), not a real episode count. This mirrors the
    frontend's buildCheckpointSequence(...).indexOf(checkpoint) + 1 exactly, so
    profile progress stats never drift from what ProgressSlider itself renders.

    Clamped to [0, total_episodes] rather than raising when season/episode fall
    outside season_episode_counts (e.g. a checkpoint saved before a re-ingest
    changed the season layout) — a display stat shouldn't 500 the profile page
    over stale data.
    """
    season, episode = parse_checkpoint(checkpoint)
    total_episodes = sum(season_episode_counts)
    if season < 1 or not season_episode_counts:
        return 0
    absolute = sum(season_episode_counts[: season - 1]) + episode
    return max(0, min(absolute, total_episodes))


def min_checkpoint(checkpoints: Iterable[str]) -> str:
    """Return the earliest checkpoint in a group (SPEC.md D3: effective_checkpoint = min(C_1..C_n))."""
    checkpoints = list(checkpoints)
    if not checkpoints:
        raise InvalidCheckpointError("At least one checkpoint is required to compute a minimum.")
    return min(checkpoints, key=parse_checkpoint)


def filter_visible_facts(
    facts: Iterable[TemporalFact], user_checkpoint: str
) -> list[TemporalFact]:
    """Return only the facts revealed at or before the given checkpoint."""
    checkpoint_value = parse_checkpoint(user_checkpoint)
    return [
        fact
        for fact in facts
        if parse_checkpoint(fact.first_revealed_at) <= checkpoint_value
    ]
