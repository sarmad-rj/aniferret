"""Tests for the franchise watch-order endpoint (app/services/franchise_service.py):
release order and chronological order are independent ranks that can genuinely
diverge (a prequel entry released after the show it precedes), and a tracked entry
must resolve its dossier's anime_slug while an untracked entry stays null.
"""

from fastapi.testclient import TestClient


def test_watch_order_unknown_franchise_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/franchises/no-such-franchise/watch-order")

    assert response.status_code == 404


def test_watch_order_returns_entries_with_diverging_orders(client: TestClient) -> None:
    response = client.get("/api/v1/franchises/code-geass/watch-order")

    assert response.status_code == 200
    body = response.json()
    assert body["franchise_slug"] == "code-geass"
    assert len(body["entries"]) == 2

    by_title = {entry["title"]: entry for entry in body["entries"]}
    tv_entry = by_title["Code Geass: Lelouch of the Rebellion"]
    ova_entry = by_title["Code Geass: Akito the Exiled (OVA)"]

    assert tv_entry["release_order"] < ova_entry["release_order"]
    assert tv_entry["chronological_order"] > ova_entry["chronological_order"]


def test_watch_order_resolves_anime_slug_only_for_tracked_entries(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/franchises/code-geass/watch-order")

    assert response.status_code == 200
    entries = {entry["title"]: entry for entry in response.json()["entries"]}

    assert entries["Code Geass: Lelouch of the Rebellion"]["anime_slug"] == "code-geass"
    assert entries["Code Geass: Akito the Exiled (OVA)"]["anime_slug"] is None
    assert entries["Code Geass: Akito the Exiled (OVA)"]["note"] is not None


def test_watch_order_entries_sorted_by_release_order(client: TestClient) -> None:
    response = client.get("/api/v1/franchises/code-geass/watch-order")

    entries = response.json()["entries"]
    release_orders = [entry["release_order"] for entry in entries]
    assert release_orders == sorted(release_orders)
