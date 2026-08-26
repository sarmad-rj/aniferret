"""Gemini-backed synthesis over already-gated Temporal Facts.

Reveal gating never happens here — by the time a fact reaches this module it has
already passed the reveal engine / vector-store pre-filter, so this module's only
job is to phrase an answer from facts it's already allowed to see. If no API key is
configured, or the call fails for any reason, callers must fall back to a
deterministic templated answer rather than surface an error (SPEC D2 requires the
refusal path to be fully deterministic and byte-identical; the LLM path is a
best-effort enhancement layered on top of it, never a replacement for it).
"""

import logging

from google import genai

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_SYSTEM_INSTRUCTION = (
    "You are AniFerret's Lore Assistant. Answer the user's question using ONLY the facts "
    "provided in the untrusted context block below. Do not use outside knowledge, and do not "
    "mention or allude to any plot point not present in that context. Cite each fact you use by "
    "its source_citation. If the provided facts do not answer the question, say so plainly — do "
    "not speculate."
)

_MODEL_NAME = "gemini-3.6-flash"


def _build_prompt(question: str, anime_title: str, facts: list[dict]) -> str:
    fact_lines = "\n".join(
        f"- {fact['subject']} {fact['predicate'].replace('_', ' ')}: {fact['object']} "
        f"(source: {fact['source_citation']})"
        for fact in facts
    )
    return (
        f"Anime: {anime_title}\n"
        f"Question: {question}\n\n"
        "[UNTRUSTED CONTEXT START]\n"
        f"{fact_lines}\n"
        "[UNTRUSTED CONTEXT END]"
    )


def synthesize_answer(question: str, anime_title: str, facts: list[dict]) -> str | None:
    """Ask Gemini to phrase an answer from already-visible facts. Returns None on any failure."""
    settings = get_settings()
    if not settings.gemini_api_key or not facts:
        return None

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=_MODEL_NAME,
            contents=_build_prompt(question, anime_title, facts),
            config={"system_instruction": _SYSTEM_INSTRUCTION},
        )
        text = (response.text or "").strip()
        return text or None
    except Exception:
        # Any Gemini/network/quota failure degrades to the deterministic template answer —
        # logged so the failure is diagnosable, but never surfaced to the caller as an error.
        logger.warning("Gemini synthesis failed; falling back to template answer.", exc_info=True)
        return None
