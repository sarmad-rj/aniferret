from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.models.watch_progress import WatchProgress
from app.schemas.profile import ProfileResponse, ProfileStats, UpdatePasswordRequest, WatchCheckpointCard
from app.services.reveal_engine import checkpoint_to_absolute_episode


class IncorrectPasswordError(ValueError):
    """Raised when a password-confirmation check (update-password, delete-account)
    fails — the account and credential are otherwise valid, this is purely a
    re-authentication failure."""


async def get_profile(db: AsyncSession, user: User) -> ProfileResponse:
    """Build the full profile payload: identity fields plus, per tracked anime, a
    checkpoint card and the aggregate stats derived from it. Ordered most-recently-
    updated first so the "Active Watch Checkpoints" list surfaces what the user is
    actually watching right now.
    """
    stmt = (
        select(WatchProgress)
        .where(WatchProgress.user_id == user.id)
        .options(selectinload(WatchProgress.anime))
        .order_by(WatchProgress.updated_at.desc())
    )
    result = await db.execute(stmt)
    progress_rows = result.scalars().all()

    checkpoints: list[WatchCheckpointCard] = []
    total_episodes_watched = 0
    for progress in progress_rows:
        anime = progress.anime
        current_episode = checkpoint_to_absolute_episode(progress.checkpoint, anime.season_episode_counts)
        total_episodes_watched += current_episode
        checkpoints.append(
            WatchCheckpointCard(
                anime_slug=anime.slug,
                anime_title=anime.title,
                cover_image_url=anime.cover_image_url,
                checkpoint=progress.checkpoint,
                current_episode=current_episode,
                total_episodes=anime.total_episodes,
            )
        )

    return ProfileResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_verified=user.is_verified,
        created_at=user.created_at,
        stats=ProfileStats(
            total_series_tracked=len(checkpoints),
            total_episodes_watched=total_episodes_watched,
        ),
        checkpoints=checkpoints,
    )


async def update_password(db: AsyncSession, user: User, payload: UpdatePasswordRequest) -> None:
    if not verify_password(payload.current_password, user.hashed_password):
        raise IncorrectPasswordError("Current password is incorrect")
    user.hashed_password = hash_password(payload.new_password)
    await db.commit()


async def delete_account(db: AsyncSession, user: User, password: str) -> None:
    """Delete the user row and, via the User.watch_progress ORM cascade (backed by
    watch_progress.user_id's ondelete=CASCADE at the DB level too), every
    WatchProgress row tied to it. There is no separate session/token store to
    invalidate — auth is a stateless JWT, so any token already issued for this user
    stops working the instant get_current_user's post-decode DB lookup finds no
    matching row, with no extra revocation step needed.
    """
    if not verify_password(password, user.hashed_password):
        raise IncorrectPasswordError("Password is incorrect")
    await db.delete(user)
    await db.commit()
