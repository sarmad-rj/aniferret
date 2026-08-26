from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="Service health status, e.g. 'ok'")
    timestamp: datetime = Field(..., description="UTC timestamp the health check was evaluated")
