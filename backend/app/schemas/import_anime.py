from pydantic import BaseModel, Field


class AnimeImportRequest(BaseModel):
    query: str = Field(
        ..., min_length=1, description="Anime title to search for, or a numeric MAL id"
    )
