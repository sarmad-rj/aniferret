from pydantic import BaseModel, ConfigDict, Field

from app.schemas.checkpoint import CHECKPOINT_PATTERN


class TemporalFactBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    subject: str = Field(..., description="Entity the fact is about, e.g. a character name")
    predicate: str = Field(..., description="Relation type, e.g. 'true_identity'")
    object: str = Field(..., description="Revealed value of the fact")
    source_citation: str = Field(..., description="Human-readable source, e.g. 'Season 1, Episode 12'")
    first_revealed_at: str = Field(..., pattern=CHECKPOINT_PATTERN, description="Checkpoint the fact becomes true, e.g. 'S1E12'")
    first_hinted_at: str | None = Field(default=None, pattern=CHECKPOINT_PATTERN, description="Checkpoint of the earliest foreshadowing, e.g. 'S1E3'")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence score")
    source: str = Field(
        default="curated", description="Origin: 'curated', 'jikan', 'anilist', or 'wiki'"
    )


class TemporalFactCreate(TemporalFactBase):
    anime_id: int


class TemporalFactRead(TemporalFactBase):
    fact_id: int
    anime_id: int
