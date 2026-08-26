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


class AnimeCreate(AnimeBase):
    pass


class AnimeRead(AnimeBase):
    id: int
