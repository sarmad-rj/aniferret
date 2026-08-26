from datetime import datetime, timezone

from fastapi import APIRouter, status

from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def get_health() -> HealthResponse:
    """Report service liveness and the current UTC timestamp."""
    return HealthResponse(status="ok", timestamp=datetime.now(timezone.utc))
