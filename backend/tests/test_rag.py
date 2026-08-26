import uuid

import chromadb
import pytest
from chromadb import EmbeddingFunction

from app.services import llm_synthesizer, query_service
from app.services.reveal_engine import checkpoint_to_ordinal
from app.services.vector_store import index_facts, semantic_search


class _FakeEmbeddingFunction(EmbeddingFunction):
    """Deterministic, offline, hash-based embedding — avoids downloading a real model in tests."""

    def __init__(self) -> None:
        pass

    @staticmethod
    def name() -> str:
        return "fake-hash-embedding"

    def __call__(self, input):
        vectors = []
        for text in input:
            vector = [0.0, 0.0, 0.0, 0.0]
            for index, char in enumerate(text):
                vector[index % 4] += ord(char)
            vectors.append(vector)
        return vectors


class _FakeFact:
    def __init__(self, fact_id, subject, predicate, obj, source_citation, first_revealed_at):
        self.fact_id = fact_id
        self.subject = subject
        self.predicate = predicate
        self.object = obj
        self.source_citation = source_citation
        self.first_revealed_at = first_revealed_at


@pytest.fixture
def collection():
    # EphemeralClient() shares its in-process store across instances by default, so each
    # test needs a uniquely-named collection to stay isolated from the others.
    client = chromadb.EphemeralClient()
    return client.get_or_create_collection(
        name=f"test_temporal_facts_{uuid.uuid4().hex}",
        embedding_function=_FakeEmbeddingFunction(),
    )


def test_checkpoint_to_ordinal_orders_numerically() -> None:
    assert checkpoint_to_ordinal("S1E9") < checkpoint_to_ordinal("S1E12")
    assert checkpoint_to_ordinal("S1E25") < checkpoint_to_ordinal("S2E1")


def test_semantic_search_excludes_facts_past_checkpoint(collection) -> None:
    fact_early = _FakeFact(1, "Lelouch", "royal_lineage", "11th prince", "S1E1", "S1E1")
    fact_late = _FakeFact(2, "Lelouch", "true_identity", "Zero", "S1E12", "S1E12")

    index_facts([(fact_early, "code-geass"), (fact_late, "code-geass")], collection=collection)

    results_before = semantic_search("who is zero", "code-geass", "S1E10", collection=collection)
    assert all(result["predicate"] != "true_identity" for result in results_before)

    results_after = semantic_search("who is zero", "code-geass", "S1E12", collection=collection)
    assert any(result["predicate"] == "true_identity" for result in results_after)


def test_semantic_search_filters_by_anime_slug(collection) -> None:
    fact_a = _FakeFact(1, "Eren", "titan_shifter_identity", "Titan", "S1E8", "S1E8")
    fact_b = _FakeFact(2, "Lelouch", "royal_lineage", "prince", "S1E1", "S1E1")

    index_facts([(fact_a, "attack-on-titan"), (fact_b, "code-geass")], collection=collection)

    results = semantic_search("Eren titan", "code-geass", "S3E25", collection=collection)
    assert all(result["subject"] != "Eren" for result in results)


def test_semantic_search_empty_collection_returns_empty(collection) -> None:
    assert semantic_search("anything", "code-geass", "S1E1", collection=collection) == []


def test_llm_synthesizer_returns_none_without_api_key(monkeypatch) -> None:
    class _FakeSettings:
        gemini_api_key = ""

    monkeypatch.setattr(llm_synthesizer, "get_settings", lambda: _FakeSettings())

    result = llm_synthesizer.synthesize_answer(
        "Who is Zero?",
        "Code Geass",
        [
            {
                "subject": "Lelouch",
                "predicate": "true_identity",
                "object": "Zero",
                "source_citation": "S1E12",
            }
        ],
    )
    assert result is None


def test_llm_synthesizer_returns_none_with_no_facts(monkeypatch) -> None:
    class _FakeSettings:
        gemini_api_key = "fake-key-for-this-test"

    monkeypatch.setattr(llm_synthesizer, "get_settings", lambda: _FakeSettings())

    assert llm_synthesizer.synthesize_answer("Who is Zero?", "Code Geass", []) is None


def test_query_endpoint_uses_llm_synthesized_answer_when_available(client, monkeypatch) -> None:
    monkeypatch.setattr(
        query_service.vector_store,
        "semantic_search",
        lambda *args, **kwargs: [
            {
                "subject": "Lelouch Lamperouge",
                "predicate": "true_identity",
                "object": "Zero, masked leader of the Black Knights.",
                "source_citation": "Season 1, Episode 12",
            }
        ],
    )
    monkeypatch.setattr(
        query_service.llm_synthesizer,
        "synthesize_answer",
        lambda *args, **kwargs: "Lelouch is secretly Zero, the masked revolutionary leader.",
    )

    response = client.post(
        "/api/v1/query",
        json={"anime_slug": "code-geass", "checkpoint": "S1E12", "question": "Who is Zero?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["locked"] is False
    assert body["answer"] == "Lelouch is secretly Zero, the masked revolutionary leader."
    assert body["citations"] == ["Season 1, Episode 12"]


def test_query_endpoint_falls_back_to_template_when_llm_unavailable(client, monkeypatch) -> None:
    monkeypatch.setattr(query_service.vector_store, "semantic_search", lambda *a, **k: [])
    monkeypatch.setattr(query_service.llm_synthesizer, "synthesize_answer", lambda *a, **k: None)

    response = client.post(
        "/api/v1/query",
        json={"anime_slug": "code-geass", "checkpoint": "S1E12", "question": "Who is Zero?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["locked"] is False
    assert "Zero" in body["answer"]


def test_query_endpoint_vector_store_exception_falls_back_to_keyword_match(
    client, monkeypatch
) -> None:
    def _raise(*args, **kwargs):
        raise RuntimeError("chroma unavailable")

    monkeypatch.setattr(query_service.vector_store, "semantic_search", _raise)
    monkeypatch.setattr(query_service.llm_synthesizer, "synthesize_answer", lambda *a, **k: None)

    response = client.post(
        "/api/v1/query",
        json={"anime_slug": "code-geass", "checkpoint": "S1E12", "question": "Who is Zero?"},
    )

    assert response.status_code == 200
    assert response.json()["locked"] is False
