from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings

_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: int) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=_ALGORITHM)


class InvalidTokenError(ValueError):
    """Raised when a token is missing, malformed, expired, or otherwise unusable."""


def decode_access_token(token: str) -> int:
    """Return the user id encoded in a valid access token, or raise InvalidTokenError."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[_ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise InvalidTokenError("Invalid or expired token") from exc
