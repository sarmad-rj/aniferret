from pydantic import BaseModel, ConfigDict, Field


class FactionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Faction / organization name")
    description: str | None = Field(default=None, description="Non-spoiler faction summary")
    parent_id: int | None = Field(
        default=None, description="Parent faction id for a nested Crew, e.g. Straw Hat Pirates under Pirate Crews"
    )


class FactionCreate(FactionBase):
    anime_id: int


class FactionRead(FactionBase):
    id: int
    anime_id: int
