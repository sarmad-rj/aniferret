from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_admin
from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.admin import (
    AdminAnimeDetail,
    AdminAnimeMetadataUpdateRequest,
    AdminAnimeSummary,
    AdminAnimeUpdateRequest,
    AdminBulkDeleteRequest,
    AdminBulkDeleteResult,
    AdminCharacterCheckpointUpdateRequest,
    AdminCharacterDetail,
    AdminCharacterFactionUpdateRequest,
    AdminCharacterWriteRequest,
    AdminFactCheckpointUpdateRequest,
    AdminFactionDetail,
    AdminFactionWriteRequest,
    AdminSystemStatus,
    AdminUserSummary,
    DataIntegrityReport,
)
from app.schemas.auth import MessageResponse
from app.services.admin_service import (
    AnimeNotFoundError,
    CannotModifySelfError,
    CharacterNotFoundError,
    FactionNotFoundError,
    FactNotFoundError,
    InvalidFactionHierarchyError,
    InvalidFixError,
    UserNotFoundError,
    bulk_delete_anime,
    bulk_delete_users,
    create_character,
    create_faction,
    delete_anime,
    delete_character,
    delete_faction,
    delete_user,
    fix_anime_episode_counts,
    fix_character_checkpoint,
    fix_character_faction,
    fix_fact_checkpoint,
    get_anime_detail,
    get_data_integrity_report,
    list_anime_characters,
    list_anime_factions,
    list_anime_summaries,
    list_user_summaries,
    mark_user_verified,
    update_anime_metadata,
    update_character,
    update_faction,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/anime", response_model=list[AdminAnimeSummary], status_code=status.HTTP_200_OK)
async def list_admin_anime(
    _admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> list[AdminAnimeSummary]:
    return await list_anime_summaries(db)


@router.delete("/anime/{anime_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_admin_anime(
    anime_id: int,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        await delete_anime(db, anime_id)
    except AnimeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/anime/bulk-delete", response_model=AdminBulkDeleteResult, status_code=status.HTTP_200_OK
)
async def bulk_remove_admin_anime(
    payload: AdminBulkDeleteRequest,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminBulkDeleteResult:
    deleted_ids, failed = await bulk_delete_anime(db, payload.ids)
    return AdminBulkDeleteResult(deleted_ids=deleted_ids, failed=failed)


@router.get("/users", response_model=list[AdminUserSummary], status_code=status.HTTP_200_OK)
async def list_admin_users(
    _admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> list[AdminUserSummary]:
    return await list_user_summaries(db)


@router.put("/users/{user_id}/verify", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def verify_admin_user(
    user_id: int,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    try:
        await mark_user_verified(db, user_id)
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc
    return MessageResponse(message="User marked as verified.")


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_admin_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        await delete_user(db, admin, user_id)
    except CannotModifySelfError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail={"message": str(exc)}
        ) from exc
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/users/bulk-delete", response_model=AdminBulkDeleteResult, status_code=status.HTTP_200_OK
)
async def bulk_remove_admin_users(
    payload: AdminBulkDeleteRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminBulkDeleteResult:
    deleted_ids, failed = await bulk_delete_users(db, admin, payload.ids)
    return AdminBulkDeleteResult(deleted_ids=deleted_ids, failed=failed)


@router.get("/system-status", response_model=AdminSystemStatus, status_code=status.HTTP_200_OK)
async def read_admin_system_status(
    _admin: User = Depends(get_current_admin),
) -> AdminSystemStatus:
    settings = get_settings()
    return AdminSystemStatus(
        email_configured=bool(settings.resend_api_key and settings.emails_from)
    )


@router.get(
    "/data-integrity", response_model=DataIntegrityReport, status_code=status.HTTP_200_OK
)
async def read_data_integrity_report(
    _admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> DataIntegrityReport:
    return await get_data_integrity_report(db)


@router.patch(
    "/anime/{anime_id}/episode-counts",
    response_model=AdminAnimeSummary,
    status_code=status.HTTP_200_OK,
)
async def fix_admin_anime_episode_counts(
    anime_id: int,
    payload: AdminAnimeUpdateRequest,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminAnimeSummary:
    try:
        return await fix_anime_episode_counts(
            db, anime_id, payload.total_episodes, payload.season_episode_counts
        )
    except AnimeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc
    except InvalidFixError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"message": str(exc)}
        ) from exc


@router.patch(
    "/characters/{character_id}/checkpoint",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def fix_admin_character_checkpoint(
    character_id: int,
    payload: AdminCharacterCheckpointUpdateRequest,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    try:
        await fix_character_checkpoint(db, character_id, payload.first_revealed_at)
    except CharacterNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc
    except InvalidFixError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"message": str(exc)}
        ) from exc
    return MessageResponse(message="Character checkpoint updated.")


@router.patch(
    "/facts/{fact_id}/checkpoint",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def fix_admin_fact_checkpoint(
    fact_id: int,
    payload: AdminFactCheckpointUpdateRequest,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    try:
        await fix_fact_checkpoint(db, fact_id, payload.field, payload.checkpoint)
    except FactNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc
    except InvalidFixError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"message": str(exc)}
        ) from exc
    return MessageResponse(message="Fact checkpoint updated.")


@router.get(
    "/anime/{anime_id}/factions",
    response_model=list[AdminFactionDetail],
    status_code=status.HTTP_200_OK,
)
async def read_admin_anime_factions(
    anime_id: int,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminFactionDetail]:
    try:
        return await list_anime_factions(db, anime_id)
    except AnimeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc


@router.patch(
    "/characters/{character_id}/faction",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def fix_admin_character_faction(
    character_id: int,
    payload: AdminCharacterFactionUpdateRequest,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    try:
        await fix_character_faction(db, character_id, payload.faction_id)
    except (CharacterNotFoundError, FactionNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc
    except InvalidFixError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"message": str(exc)}
        ) from exc
    return MessageResponse(message="Character faction updated.")


@router.get(
    "/anime/{anime_id}/detail", response_model=AdminAnimeDetail, status_code=status.HTTP_200_OK
)
async def read_admin_anime_detail(
    anime_id: int,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminAnimeDetail:
    try:
        return await get_anime_detail(db, anime_id)
    except AnimeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc


@router.patch(
    "/anime/{anime_id}/metadata", response_model=AdminAnimeDetail, status_code=status.HTTP_200_OK
)
async def update_admin_anime_metadata(
    anime_id: int,
    payload: AdminAnimeMetadataUpdateRequest,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminAnimeDetail:
    try:
        return await update_anime_metadata(
            db,
            anime_id,
            payload.title,
            payload.cover_image_url,
            payload.genres,
            payload.synopsis,
            payload.score,
        )
    except AnimeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc


@router.post(
    "/anime/{anime_id}/factions",
    response_model=AdminFactionDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_admin_faction(
    anime_id: int,
    payload: AdminFactionWriteRequest,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminFactionDetail:
    try:
        return await create_faction(
            db, anime_id, payload.name, payload.description, payload.parent_id,
            payload.first_revealed_at,
        )
    except (AnimeNotFoundError, FactionNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc
    except InvalidFactionHierarchyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"message": str(exc)}
        ) from exc


@router.patch(
    "/factions/{faction_id}", response_model=AdminFactionDetail, status_code=status.HTTP_200_OK
)
async def update_admin_faction(
    faction_id: int,
    payload: AdminFactionWriteRequest,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminFactionDetail:
    try:
        return await update_faction(
            db, faction_id, payload.name, payload.description, payload.parent_id,
            payload.first_revealed_at,
        )
    except FactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc
    except InvalidFactionHierarchyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"message": str(exc)}
        ) from exc


@router.delete("/factions/{faction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_admin_faction(
    faction_id: int,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        await delete_faction(db, faction_id)
    except FactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/anime/{anime_id}/characters",
    response_model=list[AdminCharacterDetail],
    status_code=status.HTTP_200_OK,
)
async def read_admin_anime_characters(
    anime_id: int,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminCharacterDetail]:
    try:
        return await list_anime_characters(db, anime_id)
    except AnimeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc


@router.post(
    "/anime/{anime_id}/characters",
    response_model=AdminCharacterDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_admin_character(
    anime_id: int,
    payload: AdminCharacterWriteRequest,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminCharacterDetail:
    try:
        return await create_character(
            db, anime_id, payload.name, payload.role, payload.height, payload.avatar_url,
            payload.bounty, payload.power, payload.backstory, payload.faction_id,
            payload.first_revealed_at,
        )
    except (AnimeNotFoundError, FactionNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc
    except InvalidFixError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"message": str(exc)}
        ) from exc


@router.patch(
    "/characters/{character_id}", response_model=AdminCharacterDetail, status_code=status.HTTP_200_OK
)
async def update_admin_character(
    character_id: int,
    payload: AdminCharacterWriteRequest,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminCharacterDetail:
    try:
        return await update_character(
            db, character_id, payload.name, payload.role, payload.height, payload.avatar_url,
            payload.bounty, payload.power, payload.backstory, payload.faction_id,
            payload.first_revealed_at,
        )
    except (CharacterNotFoundError, FactionNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc
    except InvalidFixError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"message": str(exc)}
        ) from exc


@router.delete("/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_admin_character(
    character_id: int,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        await delete_character(db, character_id)
    except CharacterNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(exc)}
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
