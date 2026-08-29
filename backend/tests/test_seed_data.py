"""Guards against a class of bug found while adding One Piece: if a fact's checkpoint
episode number exceeds its season's declared length in season_episode_counts, a later
checkpoint can prematurely satisfy it. is_revealed() compares (season, episode) tuples
with no notion of season length, so e.g. a fact gated at 'S4E130' with season 4 only
130 episodes long is fine, but at only 39 episodes long, checkpoint 'S5E1' would
incorrectly satisfy it — (4, 130) <= (5, 1) is True regardless of the episode number.
"""

import pytest

from app.db.seed import SEED_ANIME
from app.services.reveal_engine import parse_checkpoint


def _iter_seed_checkpoints():
    for anime_data in SEED_ANIME:
        for fact in anime_data["facts"]:
            for checkpoint_key in ("first_revealed_at", "first_hinted_at"):
                checkpoint = fact.get(checkpoint_key)
                if checkpoint is not None:
                    yield anime_data, fact, checkpoint_key, checkpoint


@pytest.mark.parametrize(
    "anime_data,fact,checkpoint_key,checkpoint",
    list(_iter_seed_checkpoints()),
    ids=[
        f"{a['slug']}:{f['subject']}:{k}={c}" for a, f, k, c in _iter_seed_checkpoints()
    ],
)
def test_seed_checkpoint_fits_within_its_seasons_episode_count(
    anime_data, fact, checkpoint_key, checkpoint
) -> None:
    season_counts = anime_data["season_episode_counts"]
    season, episode = parse_checkpoint(checkpoint)

    assert 1 <= season <= len(season_counts), (
        f"{anime_data['slug']}: {fact['subject']}.{checkpoint_key}={checkpoint} references "
        f"season {season}, but season_episode_counts only has {len(season_counts)} seasons"
    )
    assert episode <= season_counts[season - 1], (
        f"{anime_data['slug']}: {fact['subject']}.{checkpoint_key}={checkpoint} exceeds "
        f"season {season}'s declared length of {season_counts[season - 1]} episodes"
    )
