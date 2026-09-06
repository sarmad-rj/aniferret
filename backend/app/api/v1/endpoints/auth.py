from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserRead,
    VerifyEmailRequest,
)
from app.services import email_service
from app.services.auth_service import (
    EmailAlreadyRegisteredError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidResetTokenError,
    InvalidVerificationTokenError,
    authenticate_user,
    register_user,
    request_password_reset,
    resend_verification_email,
    reset_password,
    verify_email,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_UNVERIFIED_LOGIN_MESSAGE = "Please verify your email address before logging in."
_RESET_REQUESTED_MESSAGE = "If an account exists, a reset link has been sent."
_RESEND_VERIFICATION_MESSAGE = (
    "If an unverified account exists, a new verification link has been sent."
)


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def register(
    request: Request,
    payload: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Create an account. Registration no longer doubles as login — the account
    starts unverified, and login is blocked until the emailed link is clicked."""
    try:
        user, token = await register_user(db, payload)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail={"message": str(exc)}
        ) from exc

    background_tasks.add_task(email_service.send_verification_email, user.email, token)
    return MessageResponse(
        message="Registration successful. Please check your email to verify your account."
    )


@router.post("/verify-email", response_model=TokenResponse, status_code=status.HTTP_200_OK)
@limiter.limit("20/hour")
async def verify_email_endpoint(
    request: Request, payload: VerifyEmailRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    try:
        return await verify_email(db, payload.token)
    except InvalidVerificationTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"message": str(exc)}
        ) from exc


@router.post(
    "/resend-verification", response_model=MessageResponse, status_code=status.HTTP_200_OK
)
@limiter.limit("5/hour")
async def resend_verification(
    request: Request,
    payload: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Always responds identically whether or not the email is registered or
    already verified — distinguishing those would let this endpoint enumerate
    accounts. Issues a fresh token each call, so this also covers an expired link,
    not just one that never arrived."""
    result = await resend_verification_email(db, payload.email)
    if result is not None:
        user, token = result
        background_tasks.add_task(email_service.send_verification_email, user.email, token)
    return MessageResponse(message=_RESEND_VERIFICATION_MESSAGE)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def login(
    request: Request, payload: LoginRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    try:
        return await authenticate_user(db, payload)
    except EmailNotVerifiedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail={"message": str(exc)}
        ) from exc
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail={"message": str(exc)}
        ) from exc


@router.post("/forgot-password", response_model=MessageResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/hour")
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Always responds identically whether or not the email is registered —
    distinguishing the two would let this endpoint enumerate accounts."""
    result = await request_password_reset(db, payload.email)
    if result is not None:
        user, token = result
        background_tasks.add_task(email_service.send_password_reset_email, user.email, token)
    return MessageResponse(message=_RESET_REQUESTED_MESSAGE)


@router.post("/reset-password", response_model=MessageResponse, status_code=status.HTTP_200_OK)
@limiter.limit("10/hour")
async def reset_password_endpoint(
    request: Request, payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    try:
        await reset_password(db, payload.token, payload.new_password)
    except InvalidResetTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"message": str(exc)}
        ) from exc
    return MessageResponse(message="Password reset successfully. You can now log in.")


@router.get("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
async def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
