from pydantic import BaseModel

from app.schemas.checkpoint import CheckpointStr


class WatchProgressEntry(BaseModel):
    anime_slug: str
    checkpoint: CheckpointStr


class WatchProgressSyncRequest(BaseModel):
    entries: list[WatchProgressEntry]


class WatchProgressResponse(BaseModel):
    entries: list[WatchProgressEntry]
