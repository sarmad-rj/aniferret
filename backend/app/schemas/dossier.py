from pydantic import BaseModel, ConfigDict, Field

from app.schemas.checkpoint import CHECKPOINT_PATTERN


class RevealedFact(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fact_id: int
    subject: str
    predicate: str
    object: str
    source_citation: str
    first_revealed_at: str
    first_hinted_at: str | None = None
    """Safe to expose once a fact is already revealed — the hint always precedes its own payoff."""


class CharacterDossierEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    faction_id: int | None
    role: str | None = None
    height: str | None = None
    avatar_url: str | None = None
    is_revealed: bool = Field(
        default=True,
        description=(
            "Always true: characters not yet introduced (first_revealed_at > checkpoint) "
            "are omitted from the dossier entirely rather than included masked."
        ),
    )
    first_revealed_at: str
    bounty: str | None = None
    power: str | None = Field(default=None, description="Devil Fruit / special ability")
    backstory: str | None = None
    revealed_facts: list[RevealedFact] = Field(default_factory=list)


class FactionDossierEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    parent_id: int | None = None
    revealed_facts: list[RevealedFact] = Field(default_factory=list)


class DossierResponse(BaseModel):
    anime_id: int
    anime_slug: str
    anime_title: str
    checkpoint: str = Field(..., pattern=CHECKPOINT_PATTERN)
    characters: list[CharacterDossierEntry]
    factions: list[FactionDossierEntry]
    locked_facts_count: int = Field(..., ge=0, description="Count of facts not yet revealed at this checkpoint")
