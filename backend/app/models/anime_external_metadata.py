from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class AnimeExternalMetadata(TimestampMixin, Base):
    """A per-provider snapshot of an anime's metadata, for source-conflict surfacing (SPEC.md D6)."""

    __tablename__ = "anime_external_metadata"

    id: Mapped[int] = mapped_column(primary_key=True)
    anime_id: Mapped[int] = mapped_column(
        ForeignKey("anime.id", ondelete="CASCADE"), index=True
    )
    source: Mapped[str] = mapped_column(String(20), index=True)
    """Provider tag: 'jikan' or 'anilist'."""
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    episodes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)

    anime: Mapped["Anime"] = relationship(back_populates="external_metadata")
