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
        assert api.SESSION_COOKIE in response.cookies
        names = data["brawler_names"]
        assert len(names) >= 100
        assert names == sorted(names, key=str.casefold)


def test_home_resumes_same_session_via_cookie() -> None:
    with TestClient(api.app) as client:
        first = client.get("/").json()
        second = client.get("/").json()
        assert first["session_id"] == second["session_id"]
        assert second["state"]["history"] == []


def test_home_resumes_with_history_after_guess() -> None:
    with TestClient(api.app) as client:
        session_id = client.get("/").json()["session_id"]
        answer = api.catalog.get_by_name("Shelly")
        assert answer is not None
        api.sessions[session_id] = GameSession.new(api.catalog, answer=answer)

        assert client.post("/guess", json={"guess": "Colt"}).status_code == 200

        resumed = client.get("/").json()
        assert resumed["session_id"] == session_id
        assert resumed["state"]["guess_count"] == 1
        assert len(resumed["state"]["history"]) == 1
        assert resumed["state"]["history"][0]["guess_name"] == "Colt"


def test_home_new_session_without_cookie() -> None:
    with TestClient(api.app) as client:
        first_id = client.get("/").json()["session_id"]

    with TestClient(api.app) as client:
        second_id = client.get("/").json()["session_id"]
        assert second_id != first_id


def test_home_stale_cookie_creates_new_session() -> None:
    with TestClient(api.app) as client:
        stale_id = "not-a-real-session"
        client.cookies.set(api.SESSION_COOKIE, stale_id)
        response = client.get("/")
        data = response.json()
        assert data["session_id"] != stale_id
        assert data["session_id"] in api.sessions
        assert response.cookies.get(api.SESSION_COOKIE) == data["session_id"]


def test_guess_incorrect_then_win() -> None:
    with TestClient(api.app) as client:
        session_id = client.get("/").json()["session_id"]

        answer = api.catalog.get_by_name("Shelly")
        assert answer is not None
        api.sessions[session_id] = GameSession.new(api.catalog, answer=answer)

        miss = client.post("/guess", json={"guess": "Colt"})
        assert miss.status_code == 200
        miss_data = miss.json()
        assert miss_data["result"]["correct"] is False
        assert miss_data["result"]["guess_name"] == "Colt"
        assert miss_data["status"] == "in_progress"
        assert miss_data["guess_count"] == 1
        assert miss_data["answer_name"] is None
        assert "state" not in miss_data
        assert "history" not in miss_data

        win = client.post("/guess", json={"guess": "shelly"})
        assert win.status_code == 200
        win_data = win.json()
        assert win_data["result"]["correct"] is True
        assert win_data["status"] == "won"
        assert win_data["guess_count"] == 2
        assert win_data["answer_name"] == "Shelly"


def test_guess_unknown_brawler() -> None:
    with TestClient(api.app) as client:
        client.get("/")
        response = client.post("/guess", json={"guess": "TotallyFake"})
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "Unknown brawler" in detail["message"]


def test_guess_missing_cookie() -> None:
    with TestClient(api.app) as client:
        # Load catalog via lifespan without setting a cookie on this client path.
        client.get("/")
        client.cookies.clear()
        response = client.post("/guess", json={"guess": "Shelly"})
        assert response.status_code == 404


def test_guess_after_win_conflict() -> None:
    with TestClient(api.app) as client:
        session_id = client.get("/").json()["session_id"]
        answer = api.catalog.get_by_name("Shelly")
        assert answer is not None
        api.sessions[session_id] = GameSession.new(api.catalog, answer=answer)

        assert client.post("/guess", json={"guess": "Shelly"}).status_code == 200
        response = client.post("/guess", json={"guess": "Colt"})
        assert response.status_code == 409


def test_guess_malformed_body() -> None:
    with TestClient(api.app) as client:
        client.get("/")
        response = client.post("/guess", json={})
        assert response.status_code == 422


def test_new_game_resets_state_keeps_session_cookie() -> None:
    with TestClient(api.app) as client:
        session_id = client.get("/").json()["session_id"]
        cookie_before = client.cookies.get(api.SESSION_COOKIE)
        assert cookie_before == session_id

        answer = api.catalog.get_by_name("Shelly")
        assert answer is not None
        api.sessions[session_id] = GameSession.new(api.catalog, answer=answer)
        assert client.post("/guess", json={"guess": "Shelly"}).status_code == 200

        response = client.post("/new")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["state"]["status"] == "in_progress"
        assert data["state"]["guess_count"] == 0
        assert data["state"]["history"] == []
        assert data["state"]["answer_name"] is None
        assert client.cookies.get(api.SESSION_COOKIE) == cookie_before
        assert response.headers.get("set-cookie") is None


def test_new_game_missing_cookie() -> None:
    with TestClient(api.app) as client:
        client.get("/")
        client.cookies.clear()
        response = client.post("/new")
        assert response.status_code == 404
