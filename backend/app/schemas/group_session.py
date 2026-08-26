from pydantic import BaseModel, Field

from app.schemas.checkpoint import CheckpointStr


class GroupSessionRequest(BaseModel):
    checkpoints: list[CheckpointStr] = Field(
        ..., min_length=1, description="One watch checkpoint per co-watcher"
    )


class GroupSessionResponse(BaseModel):
    effective_checkpoint: CheckpointStr = Field(
        ..., description="min(checkpoints) — the lowest-common checkpoint safe for the whole group"
    )
    checkpoints: list[CheckpointStr]
