from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class TemporalFact(TimestampMixin, Base):
    """An atomic, checkpoint-labeled fact — the unit the reveal engine gates on."""

    __tablename__ = "temporal_fact"

    fact_id: Mapped[int] = mapped_column(primary_key=True)
    anime_id: Mapped[int] = mapped_column(
        ForeignKey("anime.id", ondelete="CASCADE"), index=True
    )
    subject: Mapped[str] = mapped_column(String(255), index=True)
    predicate: Mapped[str] = mapped_column(String(255))
    object: Mapped[str] = mapped_column(String(500))
    source_citation: Mapped[str] = mapped_column(String(255))
    first_revealed_at: Mapped[str] = mapped_column(String(20), index=True)
    first_hinted_at: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(20), default="curated")
    """Origin of this fact: 'curated' (hand-authored), 'jikan', 'anilist', or 'wiki' (SPEC.md D6)."""

    anime: Mapped["Anime"] = relationship(back_populates="facts")
