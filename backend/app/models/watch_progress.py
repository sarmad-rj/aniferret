from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class WatchProgress(TimestampMixin, Base):
    __tablename__ = "watch_progress"
    __table_args__ = (UniqueConstraint("user_id", "anime_id", name="uq_watch_progress_user_anime"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True
    )
    anime_id: Mapped[int] = mapped_column(
        ForeignKey("anime.id", ondelete="CASCADE"), index=True
    )
    checkpoint: Mapped[str] = mapped_column(String(20))

    user: Mapped["User"] = relationship(back_populates="watch_progress")
    anime: Mapped["Anime"] = relationship()
