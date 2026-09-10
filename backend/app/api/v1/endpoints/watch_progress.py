from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.mal_import import MalImportResponse
from app.schemas.watch_progress import WatchProgressResponse, WatchProgressSyncRequest
from app.services.mal_import_service import MAX_UPLOAD_SIZE_BYTES, MalImportError, import_mal_export
from app.services.watch_progress_service import (
    UnknownAnimeSlugError,
    get_watch_progress,
    upsert_watch_progress,
)

router = APIRouter(prefix="/me/watch-progress", tags=["watch-progress"])

_ALLOWED_MAL_EXPORT_SUFFIXES = (".xml", ".xml.gz")


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


@router.post("/import-mal", response_model=MalImportResponse, status_code=status.HTTP_200_OK)
async def import_mal_watch_progress(
    file: UploadFile = File(..., description="MyAnimeList XML export (.xml or .xml.gz)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MalImportResponse:
    filename = (file.filename or "").lower()
    if not filename.endswith(_ALLOWED_MAL_EXPORT_SUFFIXES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Only .xml or .xml.gz MyAnimeList export files are supported."},
        )

    raw_bytes = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)

    try:
        return await import_mal_export(db, current_user.id, raw_bytes)
    except MalImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"message": str(exc)}
        ) from exc
