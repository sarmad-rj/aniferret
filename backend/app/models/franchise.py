from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Franchise(TimestampMixin, Base):
    __tablename__ = "franchise"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    """Deliberately equal to the matching Anime.slug for the launch corpus (e.g.
    franchise 'one-piece' pairs with anime 'one-piece'), so the frontend can fetch
    watch-order data using the anime slug it already has selected, with no extra
    lookup step."""
    name: Mapped[str] = mapped_column(String(255))

    entries: Mapped[list["FranchiseEntry"]] = relationship(
        back_populates="franchise", cascade="all, delete-orphan"
    )
