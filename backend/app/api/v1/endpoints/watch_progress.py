from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.watch_progress import WatchProgressResponse, WatchProgressSyncRequest
from app.services.watch_progress_service import (
    UnknownAnimeSlugError,
    get_watch_progress,
    upsert_watch_progress,
)

router = APIRouter(prefix="/me/watch-progress", tags=["watch-progress"])


@router.get("", response_model=WatchProgressResponse, status_code=status.HTTP_200_OK)
async def read_watch_progress(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> WatchProgressResponse:
    return await get_watch_progress(db, current_user.id)


@router.put("", response_model=WatchProgressResponse, status_code=status.HTTP_200_OK)
async def write_watch_progress(
    payload: WatchProgressSyncRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WatchProgressResponse:
    try:
        return await upsert_watch_progress(db, current_user.id, payload.entries)
    except UnknownAnimeSlugError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"message": str(exc)}
        ) from exc
