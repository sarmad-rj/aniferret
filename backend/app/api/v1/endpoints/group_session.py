from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.schemas.group_session import GroupSessionRequest, GroupSessionResponse
from app.services.reveal_engine import InvalidCheckpointError, min_checkpoint

router = APIRouter(tags=["group-session"])


@router.post(
    "/group-session/evaluate",
    response_model=GroupSessionResponse,
    status_code=status.HTTP_200_OK,
)
async def evaluate_group_session(
    payload: GroupSessionRequest, current_user: User = Depends(get_current_user)
) -> GroupSessionResponse:
    """Compute the effective (lowest-common) checkpoint for a group of co-watchers
    (SPEC.md D3). Requires an account — Group Mode creates/joins a shared watch room,
    which only makes sense tied to an identity."""
    try:
        effective = min_checkpoint(payload.checkpoints)
    except InvalidCheckpointError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"message": str(exc)}
        ) from exc

    return GroupSessionResponse(effective_checkpoint=effective, checkpoints=payload.checkpoints)
