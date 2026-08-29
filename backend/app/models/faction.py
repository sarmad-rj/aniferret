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

    anime: Mapped["Anime"] = relationship(back_populates="factions")
    characters: Mapped[list["Character"]] = relationship(back_populates="faction")
    parent: Mapped["Faction | None"] = relationship(
        back_populates="children", remote_side=[id]
    )
    children: Mapped[list["Faction"]] = relationship(back_populates="parent")
