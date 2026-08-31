from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class FranchiseEntry(TimestampMixin, Base):
    __tablename__ = "franchise_entry"

    id: Mapped[int] = mapped_column(primary_key=True)
    franchise_id: Mapped[int] = mapped_column(
        ForeignKey("franchise.id", ondelete="CASCADE"), index=True
    )
    anime_id: Mapped[int | None] = mapped_column(
        ForeignKey("anime.id", ondelete="SET NULL"), index=True, nullable=True
    )
    """Set only when this entry corresponds to one of our dossier-tracked shows. Null
    for informational-only entries (a movie/OVA we list for watch-order guidance but
    haven't built a spoiler dossier for)."""
    title: Mapped[str] = mapped_column(String(255))
    entry_type: Mapped[str] = mapped_column(String(20))
    """'tv' / 'movie' / 'ova'."""
    release_order: Mapped[int] = mapped_column(Integer)
    """Position in real-world release date order, 1-indexed within the franchise."""
    chronological_order: Mapped[int] = mapped_column(Integer)
    """Position in in-story chronological order, 1-indexed within the franchise. Can
    differ from release_order, e.g. a prequel OVA released after the show it precedes."""
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    """Real watch-order guidance, e.g. spoiler warnings or canon-branching context —
    not just a rank number."""

    franchise: Mapped["Franchise"] = relationship(back_populates="entries")
    anime: Mapped["Anime | None"] = relationship(back_populates="franchise_entries")
