from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.profile import DeleteAccountRequest, ProfileResponse, UpdatePasswordRequest
from app.services.profile_service import (
    IncorrectPasswordError,
    delete_account,
    get_profile,
    update_password,
)

router = APIRouter(prefix="/me", tags=["profile"])


@router.get("/profile", response_model=ProfileResponse, status_code=status.HTTP_200_OK)
async def read_profile(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> ProfileResponse:
    return await get_profile(db, current_user)


@router.put("/password", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def change_password(
    payload: UpdatePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    try:
        await update_password(db, current_user, payload)
    except IncorrectPasswordError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail={"message": str(exc)}
        ) from exc
    return MessageResponse(message="Password updated successfully.")


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def remove_account(
    payload: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        await delete_account(db, current_user, payload.password)
    except IncorrectPasswordError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail={"message": str(exc)}
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
