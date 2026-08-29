"""Automated Faction/Crew hierarchy classification for dynamically ingested characters.

Given the free-text affiliation string a character was ingested with (from a bio's
'Affiliation:' line, or Gemini's own faction guess — see ingestion_service), this maps
it onto a two-tier org chart: a top-level Faction (e.g. "Pirate Crews", "Marines & World
Government") and, where applicable, a named Crew nested under it (e.g. "Straw Hat
Pirates" under "Pirate Crews"). The mapping is keyword-driven so it classifies whatever
affiliation text ingestion happens to surface, for any anime — it never hardcodes a
per-character lookup table.
"""

import re

TOP_LEVEL_FACTIONS = (
    "Pirate Crews",
    "Marines & World Government",
    "Seven Warlords of the Sea (Shichibukai)",
    "Four Emperors (Yonko)",
    "Revolutionary Army",
)
"""Fixed top-level taxonomy the classifier resolves into — the org-chart categories
themselves are product-defined labels, not character data."""

_MARINE_RE = re.compile(r"\bmarine|world government|cipher pol|cp\d\b", re.IGNORECASE)
_REVOLUTIONARY_RE = re.compile(r"\brevolutionary army\b", re.IGNORECASE)
_WARLORD_RE = re.compile(r"\bwarlord|shichibukai\b", re.IGNORECASE)

_YONKO_CREW_RE = re.compile(
    r"\b(whitebeard|blackbeard|big mom|beast|red[- ]?hai(?:red)?|rocks)\s+pirates\b",
    re.IGNORECASE,
)
"""Crews led by a current or former Emperor of the Sea get bucketed under the Four
Emperors faction rather than the generic Pirate Crews bucket."""

_PIRATE_CREW_RE = re.compile(r"\b([\w' .-]+?\s+pirates)\b", re.IGNORECASE)
"""Generic '<Name> Pirates' crew-name extractor, used once marine/revolutionary/warlord
affiliations have been ruled out."""


def classify_affiliation(affiliation: str | None) -> tuple[str | None, str | None]:
    """Resolve a free-text affiliation into (top_level_faction, crew_name).

    crew_name is the specific named group (e.g. 'Straw Hat Pirates') to nest under the
    top-level faction; it's None when the affiliation *is* the top-level faction itself
    (e.g. a Marine has no crew tier below "Marines & World Government"). Returns
    (None, None) when the affiliation text doesn't match any known pattern — the caller
    falls back to treating it as an unclassified, flat faction.
    """
    if not affiliation or not affiliation.strip():
        return None, None
    text = affiliation.strip()

    if _MARINE_RE.search(text):
        return "Marines & World Government", None
    if _REVOLUTIONARY_RE.search(text):
        return "Revolutionary Army", None
    if _WARLORD_RE.search(text):
        return "Seven Warlords of the Sea (Shichibukai)", None

    yonko_match = _YONKO_CREW_RE.search(text)
    if yonko_match:
        return "Four Emperors (Yonko)", yonko_match.group(0).title()

    pirate_match = _PIRATE_CREW_RE.search(text)
    if pirate_match:
        return "Pirate Crews", pirate_match.group(1).strip().title()

    return None, None
