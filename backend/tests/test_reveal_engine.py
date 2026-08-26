import pytest

from app.services.reveal_engine import (
    InvalidCheckpointError,
    filter_visible_facts,
    is_revealed,
    parse_checkpoint,
)


class _FakeFact:
    def __init__(self, first_revealed_at: str) -> None:
        self.first_revealed_at = first_revealed_at


@pytest.mark.parametrize(
    ("checkpoint", "expected"),
    [
        ("S1E12", (1, 12)),
        ("s1e12", (1, 12)),
        (" S2E5 ", (2, 5)),
        ("S1E1", (1, 1)),
    ],
)
def test_parse_checkpoint_valid(checkpoint: str, expected: tuple[int, int]) -> None:
    assert parse_checkpoint(checkpoint) == expected


@pytest.mark.parametrize("checkpoint", ["", "E12", "S1", "Season1Episode12", "S1E", "SE12"])
def test_parse_checkpoint_invalid_raises(checkpoint: str) -> None:
    with pytest.raises(InvalidCheckpointError):
        parse_checkpoint(checkpoint)


def test_is_revealed_true_when_reached() -> None:
    assert is_revealed("S1E12", "S1E12") is True
    assert is_revealed("S1E12", "S1E20") is True
    assert is_revealed("S1E3", "S2E1") is True


def test_is_revealed_false_when_not_yet_reached() -> None:
    assert is_revealed("S1E12", "S1E11") is False
    assert is_revealed("S2E1", "S1E25") is False


def test_is_revealed_handles_episode_number_sorting_correctly() -> None:
    """'S1E12' < 'S1E9' is true lexicographically but must be false numerically."""
    assert is_revealed("S1E12", "S1E9") is False
    assert is_revealed("S1E9", "S1E12") is True


def test_filter_visible_facts_only_returns_revealed_ones() -> None:
    facts = [_FakeFact("S1E1"), _FakeFact("S1E12"), _FakeFact("S2E1")]

    visible = filter_visible_facts(facts, "S1E12")

    assert [fact.first_revealed_at for fact in visible] == ["S1E1", "S1E12"]


def test_filter_visible_facts_empty_when_nothing_revealed_yet() -> None:
    facts = [_FakeFact("S1E5")]

    visible = filter_visible_facts(facts, "S1E1")

    assert visible == []
