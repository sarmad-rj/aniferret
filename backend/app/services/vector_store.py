"""ChromaDB-backed vector store for semantic retrieval over Temporal Facts.

Implements SPEC.md D1 (progress-gated retrieval) and rag-vector-store.md's metadata
pre-filter rule: a fact's first_revealed_at must be checked *before* it can reach
similarity ranking or an LLM context window, never after.

Each TemporalFact is already an atomic, short unit (subject/predicate/object) — the
512-token/64-overlap chunking rule targets long-form prose lore sources, not this
fact ledger, so one fact is indexed as exactly one chunk.
"""

from functools import lru_cache

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions

from app.core.config import get_settings
from app.models.temporal_fact import TemporalFact
from app.services.reveal_engine import checkpoint_to_ordinal

_COLLECTION_NAME = "temporal_facts"


@lru_cache
def _get_client() -> chromadb.ClientAPI:
    settings = get_settings()
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)


def get_collection() -> Collection:
    """Return the persistent temporal_facts collection, creating it on first use."""
    client = _get_client()
    return client.get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=embedding_functions.DefaultEmbeddingFunction(),
    )


def _fact_document(fact: TemporalFact) -> str:
    return f"{fact.subject} {fact.predicate.replace('_', ' ')} {fact.object}"


def _fact_metadata(fact: TemporalFact, anime_slug: str) -> dict:
    return {
        "anime_slug": anime_slug,
        "subject": fact.subject,
        "predicate": fact.predicate,
        "object": fact.object,
        "source_citation": fact.source_citation,
        "revealed_ordinal": checkpoint_to_ordinal(fact.first_revealed_at),
    }


def index_facts(facts: list[tuple[TemporalFact, str]], collection: Collection | None = None) -> None:
    """Bulk-upsert (fact, anime_slug) pairs into the vector store."""
    if not facts:
        return
    target = collection if collection is not None else get_collection()
    target.upsert(
        ids=[str(fact.fact_id) for fact, _ in facts],
        documents=[_fact_document(fact) for fact, _ in facts],
        metadatas=[_fact_metadata(fact, anime_slug) for fact, anime_slug in facts],
    )


def semantic_search(
    question: str,
    anime_slug: str,
    checkpoint: str,
    n_results: int = 3,
    collection: Collection | None = None,
) -> list[dict]:
    """Semantically retrieve facts, pre-filtered so nothing past the checkpoint can surface.

    The `where` clause enforces first_revealed_at <= user_checkpoint at the metadata
    layer — locked facts are structurally excluded from the candidate set, not just
    hidden after the fact.
    """
    target = collection if collection is not None else get_collection()
    if target.count() == 0:
        return []

    results = target.query(
        query_texts=[question],
        n_results=n_results,
        where={
            "$and": [
                {"anime_slug": anime_slug},
                {"revealed_ordinal": {"$lte": checkpoint_to_ordinal(checkpoint)}},
            ]
        },
    )

    metadatas = (results.get("metadatas") or [[]])[0]
    if not metadatas:
        return []

    return [
        {
            "subject": metadata["subject"],
            "predicate": metadata["predicate"],
            "object": metadata["object"],
            "source_citation": metadata["source_citation"],
        }
        for metadata in metadatas
    ]
