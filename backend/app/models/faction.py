from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Faction(TimestampMixin, Base):
    __tablename__ = "faction"

    id: Mapped[int] = mapped_column(primary_key=True)
    anime_id: Mapped[int] = mapped_column(
        ForeignKey("anime.id", ondelete="CASCADE"), index=True
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("faction.id", ondelete="CASCADE"), index=True, nullable=True
    )
    """Self-referential link for a two-tier Faction/Crew hierarchy, e.g. Faction 'Pirate
    Crews' as parent of Crew 'Straw Hat Pirates'. Null for a top-level faction."""
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_revealed_at: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    """Checkpoint at which the faction's own existence becomes public knowledge (e.g. a
    class-ranking system explained in Episode 1), independent of whether any member
    character has debuted yet. Null preserves the legacy behavior: the faction card only
    appears once it has an introduced member (see _prune_empty_factions)."""

    anime: Mapped["Anime"] = relationship(back_populates="factions")
    characters: Mapped[list["Character"]] = relationship(back_populates="faction")
    parent: Mapped["Faction | None"] = relationship(
        back_populates="children", remote_side=[id]
    )
    children: Mapped[list["Faction"]] = relationship(back_populates="parent")
