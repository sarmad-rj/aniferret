import pytest
from fastapi.testclient import TestClient

from app.services.reveal_engine import InvalidCheckpointError, min_checkpoint


def test_min_checkpoint_returns_lowest() -> None:
    assert min_checkpoint(["S2E1", "S1E20", "S1E5"]) == "S1E5"


def test_min_checkpoint_numeric_ordering_not_lexicographic() -> None:
    """'S1E12' < 'S1E9' lexicographically but must resolve numerically to 'S1E9'."""
    assert min_checkpoint(["S1E12", "S1E9"]) == "S1E9"


def test_min_checkpoint_raises_on_empty() -> None:
    with pytest.raises(InvalidCheckpointError):
        min_checkpoint([])


def test_group_session_endpoint_rejects_unauthenticated_request(client: TestClient) -> None:
    """Group Mode requires an account — SPEC-driven behavior, not a stub gate."""
    response = client.post(
        "/api/v1/group-session/evaluate",
        json={"checkpoints": ["S1E12", "S1E5", "S2E1"]},
    )

    assert response.status_code == 401


def test_group_session_endpoint_rejects_garbage_token(client: TestClient) -> None:
    response = client.post(
        "/api/v1/group-session/evaluate",
        json={"checkpoints": ["S1E1"]},
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401


def test_group_session_endpoint_returns_minimum_checkpoint(
    client: TestClient, auth_token: str
) -> None:
    response = client.post(
        "/api/v1/group-session/evaluate",
        json={"checkpoints": ["S1E12", "S1E5", "S2E1"]},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["effective_checkpoint"] == "S1E5"
    assert body["checkpoints"] == ["S1E12", "S1E5", "S2E1"]


def test_group_session_endpoint_single_watcher(client: TestClient, auth_token: str) -> None:
    response = client.post(
        "/api/v1/group-session/evaluate",
        json={"checkpoints": ["S1E1"]},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    assert response.json()["effective_checkpoint"] == "S1E1"


def test_group_session_endpoint_rejects_malformed_checkpoint(
    client: TestClient, auth_token: str
) -> None:
    response = client.post(
        "/api/v1/group-session/evaluate",
        json={"checkpoints": ["S1E12", "not-a-checkpoint"]},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 422


def test_group_session_endpoint_rejects_empty_list(client: TestClient, auth_token: str) -> None:
    response = client.post(
        "/api/v1/group-session/evaluate",
        json={"checkpoints": []},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 422
