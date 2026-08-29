from pydantic import BaseModel, ConfigDict, Field

from app.schemas.checkpoint import CheckpointStr


class CharacterBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Character display name")
    faction_id: int | None = Field(default=None, description="Owning faction, if any")
    role: str | None = Field(default=None, description="Non-spoiler role, e.g. 'Captain'")
    height: str | None = Field(default=None, description="Non-spoiler physical stat")
    avatar_url: str | None = Field(default=None, description="Character portrait image URL")
    bounty: str | None = Field(default=None, description="Spoiler-gated bounty value")
    power: str | None = Field(default=None, description="Spoiler-gated Devil Fruit / ability")
    backstory: str | None = Field(default=None, description="Spoiler-gated backstory")
    first_revealed_at: CheckpointStr = Field(
        default="S1E1", description="Checkpoint at which spoiler-gated fields unlock"
    )


class CharacterCreate(CharacterBase):
    anime_id: int


class CharacterRead(CharacterBase):
    id: int
    anime_id: int
