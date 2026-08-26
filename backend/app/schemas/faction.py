from pydantic import BaseModel, ConfigDict, Field


class FactionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Faction / organization name")
    description: str | None = Field(default=None, description="Non-spoiler faction summary")


class FactionCreate(FactionBase):
    anime_id: int


class FactionRead(FactionBase):
    id: int
    anime_id: int
