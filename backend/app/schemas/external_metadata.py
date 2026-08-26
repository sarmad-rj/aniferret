from pydantic import BaseModel, ConfigDict


class ExternalMetadataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source: str
    title: str | None = None
    episodes: int | None = None
    score: float | None = None
    synopsis: str | None = None


class SourceConflict(BaseModel):
    field: str
    values: dict[str, str | int | float | None]


class AnimeSourcesResponse(BaseModel):
    anime_slug: str
    records: list[ExternalMetadataRead]
    conflicts: list[SourceConflict]
