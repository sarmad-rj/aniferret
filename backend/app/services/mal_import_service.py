"""Import a user's MyAnimeList XML/gzip export, match entries against AniFerret's own
Anime catalog, and bulk-sync WatchProgress checkpoints from it.

Multi-season franchises are never auto-set (see the resolution loop below): AniFerret
stores an entire franchise as one Anime row with a single mal_id, while a real MAL
export gives each season its own separate entry with its own mal_id and a
watched_episodes count relative only to that entry. A matched entry's season is
therefore unknowable from the data alone whenever the matched Anime spans more than
one season -- and since checkpoints gate spoiler-sensitive content, guessing wrong
here is a real spoiler leak, not a cosmetic bug. Those entries land in `skipped`
instead, for the user to confirm manually.
"""

import gzip
import io
import logging
from dataclasses import dataclass
from xml.etree.ElementTree import Element

import defusedxml.ElementTree as DefusedET
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.anime import Anime
from app.schemas.mal_import import MalImportedEntry, MalImportResponse, MalSkippedEntry
from app.schemas.watch_progress import WatchProgressEntry
from app.services.reveal_engine import parse_checkpoint
from app.services.slug_utils import slugify
from app.services.watch_progress_service import upsert_watch_progress

logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
_MAX_DECOMPRESSED_SIZE_BYTES = 50 * 1024 * 1024
_GZIP_MAGIC = b"\x1f\x8b"
_GZIP_CHUNK_SIZE = 1024 * 1024
_COMPLETED_STATUS = "Completed"
_AMBIGUOUS_REASON = "ambiguous_season_for_multi_season_franchise"

_ResolvedEntry = tuple[WatchProgressEntry, "_ParsedMalEntry", Anime]


class MalImportError(ValueError):
    """Structurally invalid, oversized, or malicious upload. The endpoint maps this to
    an HTTP 400 rather than letting it bubble up as a 500."""


@dataclass(frozen=True)
class _ParsedMalEntry:
    mal_id: int | None
    title: str
    watched_episodes: int
    status: str


def _decompress_if_gzipped(raw_bytes: bytes) -> bytes:
    """Detects gzip by magic bytes, not filename -- the endpoint's extension check is
    the rejection gate, not the parsing decision. Streams the decompression with a
    running size cap so a small, highly-compressed file can't be used as a
    memory-exhaustion bomb; aborts the instant the cap is crossed rather than ever
    materializing the full output."""
    if not raw_bytes.startswith(_GZIP_MAGIC):
        return raw_bytes

    chunks: list[bytes] = []
    total = 0
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(raw_bytes)) as gz:
            while True:
                chunk = gz.read(_GZIP_CHUNK_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                if total > _MAX_DECOMPRESSED_SIZE_BYTES:
                    raise MalImportError("Decompressed file exceeds the maximum allowed size.")
                chunks.append(chunk)
    except OSError as exc:
        raise MalImportError("Could not decompress the uploaded file.") from exc

    return b"".join(chunks)


def _node_text(node: Element, tag: str) -> str:
    child = node.find(tag)
    return child.text.strip() if child is not None and child.text else ""


def _parse_mal_entries(xml_bytes: bytes) -> list[_ParsedMalEntry]:
    try:
        root = DefusedET.fromstring(xml_bytes)
    except Exception as exc:
        raise MalImportError("Could not parse the uploaded file as MyAnimeList XML.") from exc

    entries: list[_ParsedMalEntry] = []
    for node in root.findall("anime"):
        title = _node_text(node, "series_title") or "(untitled entry)"

        mal_id_raw = _node_text(node, "series_animedb_id")
        mal_id = int(mal_id_raw) if mal_id_raw.isdigit() and int(mal_id_raw) > 0 else None

        watched_raw = _node_text(node, "my_watched_episodes")
        watched_episodes = int(watched_raw) if watched_raw.lstrip("-").isdigit() else 0
        watched_episodes = max(watched_episodes, 0)

        status = _node_text(node, "my_status")

        entries.append(
            _ParsedMalEntry(
                mal_id=mal_id, title=title, watched_episodes=watched_episodes, status=status
            )
        )

    return entries


def _dedupe_keep_highest_progress(resolved: list[_ResolvedEntry]) -> list[_ResolvedEntry]:
    """Two MAL entries can independently resolve to the same Anime (e.g. a mal_id match
    and a separate slug match landing on the same row) -- keep whichever has more
    progress, compared by (season, episode) via parse_checkpoint, never lexicographic
    string comparison (which would wrongly rank 'S1E9' above 'S1E12')."""
    best_by_slug: dict[str, _ResolvedEntry] = {}
    for item in resolved:
        entry, _parsed, _anime = item
        existing = best_by_slug.get(entry.anime_slug)
        if existing is None or parse_checkpoint(entry.checkpoint) > parse_checkpoint(
            existing[0].checkpoint
        ):
            best_by_slug[entry.anime_slug] = item
    return list(best_by_slug.values())


async def import_mal_export(db: AsyncSession, user_id: int, raw_bytes: bytes) -> MalImportResponse:
    if len(raw_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise MalImportError("Uploaded file exceeds the maximum allowed size.")

    xml_bytes = _decompress_if_gzipped(raw_bytes)
    entries = _parse_mal_entries(xml_bytes)

    mal_ids = {entry.mal_id for entry in entries if entry.mal_id is not None}
    anime_by_mal_id: dict[int, Anime] = {}
    if mal_ids:
        result = await db.execute(select(Anime).where(Anime.mal_id.in_(mal_ids)))
        anime_by_mal_id = {anime.mal_id: anime for anime in result.scalars().all()}

    remaining_slugs = {
        slugify(entry.title)
        for entry in entries
        if entry.mal_id is None or entry.mal_id not in anime_by_mal_id
    }
    anime_by_slug: dict[str, Anime] = {}
    if remaining_slugs:
        result = await db.execute(select(Anime).where(Anime.slug.in_(remaining_slugs)))
        anime_by_slug = {anime.slug: anime for anime in result.scalars().all()}

    matched_count = 0
    no_progress_count = 0
    skipped: list[MalSkippedEntry] = []
    unmatched: list[str] = []
    resolved: list[_ResolvedEntry] = []

    for entry in entries:
        anime = anime_by_mal_id.get(entry.mal_id) if entry.mal_id is not None else None
        if anime is None:
            anime = anime_by_slug.get(slugify(entry.title))

        if anime is None:
            unmatched.append(entry.title)
            continue

        matched_count += 1
        season_counts = anime.season_episode_counts or [anime.total_episodes]

        checkpoint: str | None = None
        if len(season_counts) == 1:
            if entry.status == _COMPLETED_STATUS:
                checkpoint = f"S1E{season_counts[0]}"
            elif entry.watched_episodes > 0:
                checkpoint = f"S1E{min(entry.watched_episodes, season_counts[0])}"
        elif entry.status == _COMPLETED_STATUS or entry.watched_episodes > 0:
            skipped.append(
                MalSkippedEntry(
                    title=entry.title,
                    anime_slug=anime.slug,
                    mal_id=entry.mal_id,
                    watched_episodes=entry.watched_episodes,
                    reason=_AMBIGUOUS_REASON,
                )
            )
            continue

        if checkpoint is None:
            no_progress_count += 1
            continue

        resolved.append(
            (WatchProgressEntry(anime_slug=anime.slug, checkpoint=checkpoint), entry, anime)
        )

    resolved = _dedupe_keep_highest_progress(resolved)

    if resolved:
        await upsert_watch_progress(db, user_id, [item[0] for item in resolved])

    imported = [
        MalImportedEntry(
            title=parsed.title,
            anime_slug=progress.anime_slug,
            checkpoint=progress.checkpoint,
            mal_id=parsed.mal_id,
        )
        for progress, parsed, _anime in resolved
    ]

    return MalImportResponse(
        total_in_file=len(entries),
        matched_count=matched_count,
        no_progress_count=no_progress_count,
        imported=imported,
        skipped=skipped,
        unmatched=unmatched,
    )
