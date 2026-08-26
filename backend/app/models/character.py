from __future__ import annotations

from sqlalchemy import ForeignKey, String
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

    anime: Mapped["Anime"] = relationship(back_populates="characters")
    faction: Mapped["Faction | None"] = relationship(back_populates="characters")
