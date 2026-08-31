from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.franchise import WatchOrderResponse
from app.services.franchise_service import FranchiseNotFoundError, get_watch_order

router = APIRouter(tags=["franchises"])


@router.get(
    "/franchises/{franchise_slug}/watch-order",
    response_model=WatchOrderResponse,
    status_code=status.HTTP_200_OK,
)
async def get_franchise_watch_order(
    franchise_slug: str, db: AsyncSession = Depends(get_db)
) -> WatchOrderResponse:
    """Return the release-order and chronological-order entry list for a franchise."""
    try:
        return await get_watch_order(db, franchise_slug)
    except FranchiseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc
