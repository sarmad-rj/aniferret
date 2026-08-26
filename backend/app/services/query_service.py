import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.temporal_fact import TemporalFact
from app.schemas.query import QueryResponse
from app.services import llm_synthesizer, vector_store
from app.services.dossier_service import get_anime_by_slug
from app.services.reveal_engine import is_revealed

UNIFORM_REFUSAL = "Lore locked. Advance your watch progress to unlock this information."
"""Byte-identical refusal for both locked-but-real and nonexistent facts (SPEC.md D2):
never let the response text distinguish 'a spoiler exists but is locked' from 'no such fact'."""

_STOPWORDS = {
    "who", "what", "when", "where", "why", "how", "is", "are", "was", "were",
    "the", "a", "an", "of", "does", "do", "did", "in", "to", "and", "for",
}


def _keywords(question: str) -> set[str]:
    words = re.findall(r"[a-zA-Z']+", question.lower())
    return {word for word in words if word not in _STOPWORDS and len(word) > 2}


def _matches(fact: TemporalFact, keywords: set[str]) -> bool:
    haystack = f"{fact.subject} {fact.predicate} {fact.object}".lower()
    return any(keyword in haystack for keyword in keywords)


def _fact_to_dict(fact: TemporalFact) -> dict:
    return {
        "subject": fact.subject,
        "predicate": fact.predicate,
        "object": fact.object,
        "source_citation": fact.source_citation,
    }


async def answer_query(
    db: AsyncSession, anime_slug: str, checkpoint: str, question: str
) -> QueryResponse:
    """Answer a lore question, gated by the reveal engine.

    Whether the response is locked is decided once, deterministically, from facts
    already gated at or below the user's checkpoint (SPEC D2) — nothing downstream
    (vector search, Gemini) can change that decision, only how a *visible* answer
    gets phrased. Facts that don't match, and facts that match but aren't revealed
    yet, both fall through to the same uniform refusal.
    """
    anime = await get_anime_by_slug(db, anime_slug)
    keywords = _keywords(question)

    candidate_facts = [fact for fact in anime.facts if _matches(fact, keywords)]
    visible_matches = [
        fact for fact in candidate_facts if is_revealed(fact.first_revealed_at, checkpoint)
    ]

    if not visible_matches:
        return QueryResponse(answer=UNIFORM_REFUSAL, citations=[], locked=True)

    try:
        semantic_matches = vector_store.semantic_search(question, anime_slug, checkpoint)
    except Exception:
        # Vector store unavailable or not yet indexed for this anime — fall back below.
        semantic_matches = []

    fact_dicts = semantic_matches or [_fact_to_dict(fact) for fact in visible_matches]

    llm_answer = llm_synthesizer.synthesize_answer(question, anime.title, fact_dicts)
    if llm_answer:
        citations = sorted({fact["source_citation"] for fact in fact_dicts})
        return QueryResponse(answer=llm_answer, citations=citations, locked=False)

    best_match = max(visible_matches, key=lambda fact: fact.confidence)
    answer = f"{best_match.subject} {best_match.predicate.replace('_', ' ')}: {best_match.object}"
    return QueryResponse(answer=answer, citations=[best_match.source_citation], locked=False)
