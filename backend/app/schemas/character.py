from pydantic import BaseModel, ConfigDict, Field


class CharacterBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Character display name")
    faction_id: int | None = Field(default=None, description="Owning faction, if any")


class CharacterCreate(CharacterBase):
    anime_id: int


class CharacterRead(CharacterBase):
    id: int
    anime_id: int
