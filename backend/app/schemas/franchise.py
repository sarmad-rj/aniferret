from pydantic import BaseModel


class FranchiseEntryRead(BaseModel):
    id: int
    title: str
    entry_type: str
    release_order: int
    chronological_order: int
    note: str | None = None
    anime_slug: str | None = None
    """Set only when this entry has a dossier-tracked Anime — lets the frontend link
    straight to /app/dossiers?anime=<slug>. Null for informational-only entries."""


class WatchOrderResponse(BaseModel):
    franchise_slug: str
    franchise_name: str
    entries: list[FranchiseEntryRead]
