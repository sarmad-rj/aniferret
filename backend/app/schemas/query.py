from pydantic import BaseModel, Field

from app.schemas.checkpoint import CHECKPOINT_PATTERN


class QueryRequest(BaseModel):
    anime_slug: str = Field(..., description="Series slug, e.g. 'code-geass'")
    checkpoint: str = Field(..., pattern=CHECKPOINT_PATTERN, description="User's watch checkpoint, e.g. 'S1E10'")
    question: str = Field(..., min_length=1, max_length=500, description="Free-text lore question")


class QueryResponse(BaseModel):
    answer: str
    citations: list[str] = Field(default_factory=list)
    locked: bool = Field(..., description="True when the uniform refusal was returned instead of a real answer")
