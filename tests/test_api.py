from __future__ import annotations

from fastapi.testclient import TestClient

from src import api
from src.session import GameSession


def test_home_starts_new_game() -> None:
    with TestClient(api.app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["brawler_count"] >= 100
        assert data["state"]["status"] == "in_progress"
        assert data["state"]["guess_count"] == 0
        assert data["state"]["history"] == []
        assert data["state"]["answer_name"] is None


def test_guess_incorrect_then_win() -> None:
    with TestClient(api.app) as client:
        home = client.get("/").json()
        session_id = home["session_id"]

        # Pin a known answer so the win path is deterministic.
        answer = api.catalog.get_by_name("Shelly")
        assert answer is not None
        api.sessions[session_id] = GameSession.new(api.catalog, answer=answer)

        miss = client.post(
            "/guess",
            json={"session_id": session_id, "guess": "Colt"},
        )
        assert miss.status_code == 200
        miss_data = miss.json()
        assert miss_data["result"]["correct"] is False
        assert miss_data["result"]["guess_name"] == "Colt"
        assert miss_data["state"]["status"] == "in_progress"
        assert miss_data["state"]["guess_count"] == 1
        assert miss_data["state"]["answer_name"] is None

        win = client.post(
            "/guess",
            json={"session_id": session_id, "guess": "shelly"},
        )
        assert win.status_code == 200
        win_data = win.json()
        assert win_data["result"]["correct"] is True
        assert win_data["state"]["status"] == "won"
        assert win_data["state"]["guess_count"] == 2
        assert win_data["state"]["answer_name"] == "Shelly"


def test_guess_unknown_brawler() -> None:
    with TestClient(api.app) as client:
        session_id = client.get("/").json()["session_id"]
        response = client.post(
            "/guess",
            json={"session_id": session_id, "guess": "TotallyFake"},
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "Unknown brawler" in detail["message"]


def test_guess_missing_session() -> None:
    with TestClient(api.app) as client:
        # Ensure lifespan loads the catalog.
        client.get("/")
        response = client.post(
            "/guess",
            json={"session_id": "not-a-real-session", "guess": "Shelly"},
        )
        assert response.status_code == 404


def test_guess_after_win_conflict() -> None:
    with TestClient(api.app) as client:
        session_id = client.get("/").json()["session_id"]
        answer = api.catalog.get_by_name("Shelly")
        assert answer is not None
        api.sessions[session_id] = GameSession.new(api.catalog, answer=answer)

        assert client.post(
            "/guess",
            json={"session_id": session_id, "guess": "Shelly"},
        ).status_code == 200

        response = client.post(
            "/guess",
            json={"session_id": session_id, "guess": "Colt"},
        )
        assert response.status_code == 409


def test_guess_malformed_body() -> None:
    with TestClient(api.app) as client:
        session_id = client.get("/").json()["session_id"]
        response = client.post("/guess", json={"session_id": session_id})
        assert response.status_code == 422
