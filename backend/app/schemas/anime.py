from pydantic import BaseModel, ConfigDict, Field


class AnimeBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str = Field(..., description="URL-safe unique identifier, e.g. 'code-geass'")
    title: str = Field(..., description="Official series title")
    total_episodes: int = Field(..., gt=0, description="Total tracked episode count")
    mal_id: int | None = Field(default=None, description="MyAnimeList / Jikan numeric ID")
    anilist_id: int | None = Field(default=None, description="AniList numeric ID")
    season_episode_counts: list[int] = Field(
        default_factory=list,
        description="Episode count per season in order, e.g. [12, 13, 12], for building valid checkpoints",
    )
    cover_image_url: str | None = Field(default=None, description="Poster/cover art URL")
    genres: list[str] = Field(default_factory=list, description="Genre tags, e.g. ['Action', 'Fantasy']")
    synopsis: str | None = Field(default=None, description="Official series-level premise blurb")
    score: float | None = Field(default=None, description="Aggregate community rating, 0-10 scale")


class AnimeCreate(AnimeBase):
    pass


class AnimeRead(AnimeBase):
    id: int
