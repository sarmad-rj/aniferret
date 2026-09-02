from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead


class EmailAlreadyRegisteredError(ValueError):
    """Raised when registering with an email that's already in use."""


class InvalidCredentialsError(ValueError):
    """Raised on login failure. Deliberately generic — never reveals whether the
    email exists, so a failed login can't be used to enumerate registered users."""


async def register_user(db: AsyncSession, payload: RegisterRequest) -> TokenResponse:
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise EmailAlreadyRegisteredError(f"{payload.email} is already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        display_name=payload.display_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


async def authenticate_user(db: AsyncSession, payload: LoginRequest) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise InvalidCredentialsError("Invalid email or password")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))
