from fastapi.testclient import TestClient

from app.services.query_service import UNIFORM_REFUSAL


def test_list_anime_returns_seeded_series(client: TestClient) -> None:
    response = client.get("/api/v1/anime")

    assert response.status_code == 200
    slugs = {item["slug"] for item in response.json()}
    assert "code-geass" in slugs


def test_dossier_hides_fact_before_checkpoint(client: TestClient) -> None:
    response = client.get("/api/v1/dossier/code-geass", params={"checkpoint": "S1E10"})

    assert response.status_code == 200
    body = response.json()
    assert body["locked_facts_count"] == 1
    lelouch = next(c for c in body["characters"] if c["name"] == "Lelouch Lamperouge")
    predicates = {fact["predicate"] for fact in lelouch["revealed_facts"]}
    assert predicates == {"royal_lineage"}


def test_dossier_reveals_fact_at_checkpoint(client: TestClient) -> None:
    response = client.get("/api/v1/dossier/code-geass", params={"checkpoint": "S1E12"})

    assert response.status_code == 200
    body = response.json()
    assert body["locked_facts_count"] == 0
    lelouch = next(c for c in body["characters"] if c["name"] == "Lelouch Lamperouge")
    predicates = {fact["predicate"] for fact in lelouch["revealed_facts"]}
    assert predicates == {"royal_lineage", "true_identity"}


def test_dossier_unknown_anime_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/dossier/no-such-anime", params={"checkpoint": "S1E1"})

    assert response.status_code == 404


def test_dossier_rejects_malformed_checkpoint(client: TestClient) -> None:
    response = client.get("/api/v1/dossier/code-geass", params={"checkpoint": "not-a-checkpoint"})

    assert response.status_code == 422


def test_query_returns_answer_when_revealed(client: TestClient) -> None:
    response = client.post(
        "/api/v1/query",
        json={"anime_slug": "code-geass", "checkpoint": "S1E12", "question": "Who is Zero?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["locked"] is False
    assert "Zero" in body["answer"]
    assert body["citations"] == ["Season 1, Episode 12"]


def test_query_returns_uniform_refusal_when_locked(client: TestClient) -> None:
    response = client.post(
        "/api/v1/query",
        json={"anime_slug": "code-geass", "checkpoint": "S1E10", "question": "Who is Zero?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["locked"] is True
    assert body["answer"] == UNIFORM_REFUSAL
    assert body["citations"] == []


def test_query_refusal_is_byte_identical_for_locked_and_nonexistent_facts(
    client: TestClient,
) -> None:
    """D2: a real-but-locked spoiler and a question with no matching fact at all
    must return the exact same refusal text, so neither can be distinguished."""
    locked_response = client.post(
        "/api/v1/query",
        json={"anime_slug": "code-geass", "checkpoint": "S1E10", "question": "Who is Zero?"},
    )
    control_response = client.post(
        "/api/v1/query",
        json={
            "anime_slug": "code-geass",
            "checkpoint": "S1E10",
            "question": "What is the weather like today?",
        },
    )

    assert locked_response.json()["answer"] == control_response.json()["answer"]
    assert locked_response.json() == control_response.json()


def test_query_unknown_anime_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/query",
        json={"anime_slug": "no-such-anime", "checkpoint": "S1E1", "question": "Anything?"},
    )

    assert response.status_code == 404
