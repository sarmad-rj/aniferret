import re

_SLUG_INVALID_CHARS_RE = re.compile(r"[^a-z0-9]+")


def slugify(title: str) -> str:
    """Normalizes a title into the same slug shape Anime rows are generated with (see
    ingestion_service._generate_unique_slug) — anything that matches an existing Anime.slug
    by title (e.g. mal_import_service's fallback match) must go through this exact function,
    since a byte-different normalization would silently produce false negatives."""
    return _SLUG_INVALID_CHARS_RE.sub("-", title.lower()).strip("-")
