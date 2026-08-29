from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Character(TimestampMixin, Base):
    __tablename__ = "character"

    id: Mapped[int] = mapped_column(primary_key=True)
    anime_id: Mapped[int] = mapped_column(
        ForeignKey("anime.id", ondelete="CASCADE"), index=True
    )
    faction_id: Mapped[int | None] = mapped_column(
        ForeignKey("faction.id", ondelete="SET NULL"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    """Non-spoiler identity info, e.g. 'Captain', 'Marine Admiral', 'Main', 'Supporting'."""
    height: Mapped[str | None] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bounty: Mapped[str | None] = mapped_column(String(100), nullable=True)
    """Spoiler-gated: masked by the reveal engine until first_revealed_at."""
    power: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """Devil Fruit / special ability. Spoiler-gated."""
    backstory: Mapped[str | None] = mapped_column(Text, nullable=True)
    """Spoiler-gated."""
    first_revealed_at: Mapped[str] = mapped_column(String(20), index=True, default="S1E1")
    """Checkpoint at which this character's spoiler-gated fields unlock, dynamically
    derived from the earliest checkpoint among their extracted Temporal Facts."""

    anime: Mapped["Anime"] = relationship(back_populates="characters")
    faction: Mapped["Faction | None"] = relationship(back_populates="characters")
