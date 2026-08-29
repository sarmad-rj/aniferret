"""Tests for the keyword-driven affiliation -> Faction/Crew hierarchy classifier
(app/services/faction_classifier.py). Ensures the taxonomy from SPEC.md's Faction
architecture is reachable from realistic bio-derived affiliation strings, and that
unrecognized affiliations fall back to a flat, unclassified faction rather than
raising or silently dropping the character.
"""

from app.services.faction_classifier import classify_affiliation


def test_classifies_marine_affiliation() -> None:
    assert classify_affiliation("Marine Headquarters") == ("Marines & World Government", None)


def test_classifies_world_government_affiliation() -> None:
    assert classify_affiliation("World Government agent") == ("Marines & World Government", None)


def test_classifies_revolutionary_army_affiliation() -> None:
    assert classify_affiliation("Revolutionary Army") == ("Revolutionary Army", None)


def test_classifies_warlord_affiliation() -> None:
    assert classify_affiliation("Former Warlord of the Sea") == (
        "Seven Warlords of the Sea (Shichibukai)",
        None,
    )


def test_classifies_straw_hat_pirates_under_pirate_crews() -> None:
    assert classify_affiliation("Straw Hat Pirates") == ("Pirate Crews", "Straw Hat Pirates")


def test_classifies_heart_pirates_under_pirate_crews() -> None:
    assert classify_affiliation("Heart Pirates") == ("Pirate Crews", "Heart Pirates")


def test_classifies_whitebeard_pirates_under_four_emperors() -> None:
    assert classify_affiliation("Whitebeard Pirates") == (
        "Four Emperors (Yonko)",
        "Whitebeard Pirates",
    )


def test_classifies_blackbeard_pirates_under_four_emperors() -> None:
    assert classify_affiliation("Blackbeard Pirates") == (
        "Four Emperors (Yonko)",
        "Blackbeard Pirates",
    )


def test_returns_none_none_for_unrecognized_affiliation() -> None:
    assert classify_affiliation("Shimotsuki Village") == (None, None)


def test_returns_none_none_for_empty_affiliation() -> None:
    assert classify_affiliation("") == (None, None)
    assert classify_affiliation(None) == (None, None)
