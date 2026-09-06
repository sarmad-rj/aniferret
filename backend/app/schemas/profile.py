from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.checkpoint import CheckpointStr


class WatchCheckpointCard(BaseModel):
    anime_slug: str
    anime_title: str
    cover_image_url: str | None = None
    checkpoint: CheckpointStr
    current_episode: int = Field(
        ..., ge=0, description="1-indexed absolute episode number across the full series"
    )
    total_episodes: int = Field(..., gt=0)


class ProfileStats(BaseModel):
    total_series_tracked: int = Field(..., ge=0)
    total_episodes_watched: int = Field(..., ge=0)


class ProfileResponse(BaseModel):
    id: int
    email: str
    display_name: str | None = None
    is_verified: bool
    created_at: datetime
    stats: ProfileStats
    checkpoints: list[WatchCheckpointCard]


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, description="Minimum 8 characters")


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., description="Current password, re-verified before the account is deleted")
