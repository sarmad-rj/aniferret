from __future__ import annotations

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Anime(TimestampMixin, Base):
    __tablename__ = "anime"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    total_episodes: Mapped[int] = mapped_column(Integer)
    mal_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    anilist_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    season_episode_counts: Mapped[list[int]] = mapped_column(JSON, default=list)
    """Episode count per season in order, e.g. [12, 13, 12], used to build valid S<season>E<episode> checkpoints."""

    characters: Mapped[list["Character"]] = relationship(
        back_populates="anime", cascade="all, delete-orphan"
    )
    factions: Mapped[list["Faction"]] = relationship(
        back_populates="anime", cascade="all, delete-orphan"
    )
    facts: Mapped[list["TemporalFact"]] = relationship(
        back_populates="anime", cascade="all, delete-orphan"
    )
    external_metadata: Mapped[list["AnimeExternalMetadata"]] = relationship(
        back_populates="anime", cascade="all, delete-orphan"
    )
