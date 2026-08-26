import pytest
from pydantic import ValidationError

from app.schemas.character import CharacterCreate, CharacterRead
from app.schemas.faction import FactionCreate, FactionRead
from app.schemas.temporal_fact import TemporalFactCreate, TemporalFactRead


def test_character_create_and_read_round_trip() -> None:
    created = CharacterCreate(name="Lelouch Lamperouge", faction_id=1, anime_id=2)
    read = CharacterRead(id=1, anime_id=2, name=created.name, faction_id=created.faction_id)

    assert read.name == "Lelouch Lamperouge"
    assert read.faction_id == 1


def test_faction_create_and_read_round_trip() -> None:
    created = FactionCreate(name="Black Knights", description="Resistance force.", anime_id=2)
    read = FactionRead(
        id=1, anime_id=2, name=created.name, description=created.description
    )

    assert read.description == "Resistance force."


def test_temporal_fact_create_rejects_malformed_checkpoint() -> None:
    with pytest.raises(ValidationError):
        TemporalFactCreate(
            anime_id=1,
            subject="Lelouch",
            predicate="true_identity",
            object="Zero",
            source_citation="S1E12",
            first_revealed_at="not-a-checkpoint",
            confidence=0.9,
        )


def test_temporal_fact_read_defaults_source_to_curated() -> None:
    fact = TemporalFactRead(
        fact_id=1,
        anime_id=1,
        subject="Lelouch",
        predicate="true_identity",
        object="Zero",
        source_citation="S1E12",
        first_revealed_at="S1E12",
        confidence=0.9,
    )

    assert fact.source == "curated"
