from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.checkpoint import CheckpointStr


class AdminAnimeSummary(BaseModel):
    id: int
    slug: str
    title: str
    total_episodes: int
    character_count: int = Field(..., ge=0)
    fact_count: int = Field(..., ge=0)


class AdminUserSummary(BaseModel):
    id: int
    email: str
    display_name: str | None = None
    is_verified: bool
    is_admin: bool
    created_at: datetime
    tracked_series_count: int = Field(..., ge=0)


class EpisodeCountMismatch(BaseModel):
    anime_id: int
    anime_slug: str
    anime_title: str
    declared_total_episodes: int
    season_episode_counts: list[int]
    season_counts_sum: int


class OutOfRangeCheckpoint(BaseModel):
    anime_slug: str
    anime_title: str
    entity_type: str = Field(..., description="'character' or 'temporal_fact'")
    entity_id: int
    entity_label: str
    field: str = Field(..., description="'first_revealed_at' or 'first_hinted_at'")
    checkpoint: str
    reason: str


class CharacterWithoutFaction(BaseModel):
    anime_id: int
    anime_slug: str
    anime_title: str
    character_id: int
    character_name: str


class DataIntegrityReport(BaseModel):
    episode_count_mismatches: list[EpisodeCountMismatch]
    out_of_range_checkpoints: list[OutOfRangeCheckpoint]
    characters_without_faction: list[CharacterWithoutFaction]


class AdminAnimeUpdateRequest(BaseModel):
    total_episodes: int = Field(..., gt=0)
    season_episode_counts: list[int] = Field(..., min_length=1)


class AdminCharacterCheckpointUpdateRequest(BaseModel):
    first_revealed_at: CheckpointStr


class AdminFactCheckpointUpdateRequest(BaseModel):
    field: Literal["first_revealed_at", "first_hinted_at"]
    checkpoint: CheckpointStr


class AdminCharacterFactionUpdateRequest(BaseModel):
    faction_id: int


class AdminAnimeDetail(BaseModel):
    id: int
    slug: str
    title: str
    total_episodes: int
    cover_image_url: str | None = None
    genres: list[str] = Field(default_factory=list)
    synopsis: str | None = None
    score: float | None = None


class AdminAnimeMetadataUpdateRequest(BaseModel):
    title: str = Field(..., min_length=1)
    cover_image_url: str | None = None
    genres: list[str] = Field(default_factory=list)
    synopsis: str | None = None
    score: float | None = Field(default=None, ge=0, le=10)


class AdminFactionDetail(BaseModel):
    id: int
    anime_id: int
    name: str
    description: str | None = None
    parent_id: int | None = None
    first_revealed_at: str | None = None


class AdminFactionWriteRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = None
    parent_id: int | None = None
    first_revealed_at: CheckpointStr | None = None


class AdminCharacterDetail(BaseModel):
    id: int
    anime_id: int
    name: str
    role: str | None = None
    height: str | None = None
    avatar_url: str | None = None
    bounty: str | None = None
    power: str | None = None
    backstory: str | None = None
    faction_id: int | None = None
    first_revealed_at: str


class AdminCharacterWriteRequest(BaseModel):
    name: str = Field(..., min_length=1)
    role: str | None = None
    height: str | None = None
    avatar_url: str | None = None
    bounty: str | None = None
    power: str | None = None
    backstory: str | None = None
    faction_id: int | None = None
    first_revealed_at: CheckpointStr = "S1E1"


class AdminSystemStatus(BaseModel):
    email_configured: bool = Field(
        ...,
        description=(
            "Whether RESEND_API_KEY/EMAILS_FROM are both set — never the values "
            "themselves. False means verification/reset emails silently no-op "
            "(logged, not sent); see email_service._send_email."
        ),
    )


class AdminBulkDeleteRequest(BaseModel):
    ids: list[int] = Field(..., min_length=1)


class AdminBulkDeleteResult(BaseModel):
    deleted_ids: list[int]
    failed: list[dict[str, str]] = Field(
        default_factory=list, description="[{'id': str(id), 'reason': str}, ...] for any that failed"
    )
