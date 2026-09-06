import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead

_VERIFICATION_TOKEN_TTL = timedelta(hours=24)
_RESET_TOKEN_TTL = timedelta(hours=1)


class EmailAlreadyRegisteredError(ValueError):
    """Raised when registering with an email that's already in use."""


class InvalidCredentialsError(ValueError):
    """Raised on login failure. Deliberately generic — never reveals whether the
    email exists, so a failed login can't be used to enumerate registered users."""


class EmailNotVerifiedError(ValueError):
    """Raised on login when credentials are correct but the account hasn't
    completed email verification yet."""


class InvalidVerificationTokenError(ValueError):
    """Raised when a verification token is missing, unknown, or expired."""


class InvalidResetTokenError(ValueError):
    """Raised when a password-reset token is missing, unknown, or expired."""


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


def _is_expired(expires_at: datetime | None) -> bool:
    """SQLite (via aiosqlite) round-trips a DateTime(timezone=True) column back as
    naive — even though it was written as UTC-aware — while Postgres would keep it
    aware; comparing a naive value against datetime.now(timezone.utc) raises
    TypeError. Every value this app ever writes to these columns is already UTC, so
    a bare naive datetime is assumed to be UTC rather than treated as ambiguous.
    Correct on both engines: an already-aware value (Postgres) passes through
    unchanged."""
    if expires_at is None:
        return True
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < datetime.now(timezone.utc)


async def register_user(db: AsyncSession, payload: RegisterRequest) -> tuple[User, str]:
    """Create an unverified account and return it alongside its verification token
    (the caller — the endpoint — owns queueing the email; this stays testable and
    free of any BackgroundTasks/transport concern)."""
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise EmailAlreadyRegisteredError(f"{payload.email} is already registered")

    token = _generate_token()
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        display_name=payload.display_name,
        is_verified=False,
        verification_token=token,
        verification_token_expires_at=datetime.now(timezone.utc) + _VERIFICATION_TOKEN_TTL,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user, token


async def authenticate_user(db: AsyncSession, payload: LoginRequest) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise InvalidCredentialsError("Invalid email or password")
    if not user.is_verified:
        raise EmailNotVerifiedError("Please verify your email address before logging in.")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


async def verify_email(db: AsyncSession, token: str) -> TokenResponse:
    result = await db.execute(select(User).where(User.verification_token == token))
    user = result.scalar_one_or_none()
    if user is None or _is_expired(user.verification_token_expires_at):
        raise InvalidVerificationTokenError("Invalid or expired verification token")

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires_at = None
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(user.id)
    return TokenResponse(access_token=access_token, user=UserRead.model_validate(user))


async def resend_verification_email(db: AsyncSession, email: str) -> tuple[User, str] | None:
    """Returns (user, token) if the email belongs to an unverified account, else
    None — the caller always responds identically either way (same enumeration-
    safety reasoning as request_password_reset), and there's nothing useful to send
    an already-verified account. Issues a brand-new token/expiry rather than reusing
    whatever's on the row, so this also covers "my old link expired"."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or user.is_verified:
        return None

    token = _generate_token()
    user.verification_token = token
    user.verification_token_expires_at = datetime.now(timezone.utc) + _VERIFICATION_TOKEN_TTL
    await db.commit()
    return user, token


async def request_password_reset(db: AsyncSession, email: str) -> tuple[User, str] | None:
    """Returns (user, token) if the email is registered, else None — the caller
    always responds identically either way (SPEC-mandated enumeration safety), so
    this only needs to distinguish "queue an email" from "don't"."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        return None

    token = _generate_token()
    user.reset_password_token = token
    user.reset_password_token_expires_at = datetime.now(timezone.utc) + _RESET_TOKEN_TTL
    await db.commit()
    return user, token


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    result = await db.execute(select(User).where(User.reset_password_token == token))
    user = result.scalar_one_or_none()
    if user is None or _is_expired(user.reset_password_token_expires_at):
        raise InvalidResetTokenError("Invalid or expired reset token")

    user.hashed_password = hash_password(new_password)
    user.reset_password_token = None
    user.reset_password_token_expires_at = None
    await db.commit()
