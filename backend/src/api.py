"""FastAPI REST layer for Brawldle.

Run from the backend/ directory:
  uvicorn src.api:app --reload
"""

from __future__ import annotations

import time
import difflib
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field

from src.catalog import BrawlerCatalog
from src.session import GameAlreadyOverError, GameSession, InvalidGuessError

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

SESSION_COOKIE = "brawldle_session"
SESSION_COOKIE_MAX_AGE = 24 * 60 * 60  # 24 hours
SESSION_TTL_SECONDS = SESSION_COOKIE_MAX_AGE  # keep server TTL in sync with the cookie

sessions: dict[str, tuple[float, GameSession]] = {}
catalog: BrawlerCatalog | None = None

def _purge_expired_sessions() -> None:
    cutoff = time.time() - SESSION_TTL_SECONDS
    expired = [sid for sid, (created_at, _) in sessions.items() if created_at < cutoff]
    for sid in expired:
        del sessions[sid]

@asynccontextmanager
async def lifespan(_app: FastAPI):
    global catalog
    catalog = BrawlerCatalog()
    yield
    sessions.clear()
    catalog = None


app = FastAPI(title="Brawldle", lifespan=lifespan)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class GuessRequest(BaseModel):
    guess: str = Field(min_length=1)


def _require_catalog() -> BrawlerCatalog:
    if catalog is None:
        raise HTTPException(status_code=503, detail="Catalog not loaded.")
    return catalog


def _get_session(session_id: str) -> GameSession:
    entry = sessions.get(session_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Unknown session_id.")
    return entry[1]


def _session_from_cookie(request: Request) -> tuple[str, GameSession]:
    session_id = request.cookies.get(SESSION_COOKIE)
    if not session_id:
        raise HTTPException(status_code=404, detail="Unknown session_id.")
    return session_id, _get_session(session_id)


def _set_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        max_age=SESSION_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        path="/",
    )


def _suggest(name: str, cat: BrawlerCatalog) -> str | None:
    matches = difflib.get_close_matches(
        name.strip(), cat.all_names(), n=1, cutoff=0.6
    )
    return matches[0] if matches else None


def _game_payload(session_id: str, session: GameSession, cat: BrawlerCatalog) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "brawler_count": len(cat),
        "brawler_names": sorted(cat.all_names(), key=str.casefold),
        "state": session.to_dict(),
    }


@app.get("/")
@limiter.limit("30/minute")
def home(request: Request, response: Response) -> dict[str, Any]:
    _purge_expired_sessions()
    cat = _require_catalog()
    cookie_id = request.cookies.get(SESSION_COOKIE)
    if cookie_id and cookie_id in sessions:
        return _game_payload(cookie_id, sessions[cookie_id][1], cat)  # unpack session

    session = GameSession.new(cat)
    session_id = str(uuid.uuid4())
    sessions[session_id] = (time.time(), session)
    _set_session_cookie(response, session_id)
    return _game_payload(session_id, session, cat)


@app.post("/new")
@limiter.limit("30/minute")
def new_game(request: Request) -> dict[str, Any]:
    """Start a fresh round under the existing session cookie (no new cookie)."""
    cat = _require_catalog()
    session_id, _old = _session_from_cookie(request)
    session = GameSession.new(cat)
    sessions[session_id] = (time.time(), session)  # store as tuple, refresh timestamp too
    return _game_payload(session_id, session, cat)

@app.post("/guess")
@limiter.limit("20/minute")
def submit_guess(request: Request, body: GuessRequest) -> dict[str, Any]:
    cat = _require_catalog()
    _session_id, session = _session_from_cookie(request)

    try:
        result = session.make_guess(body.guess)
    except InvalidGuessError:
        detail: dict[str, Any] = {"message": f"Unknown brawler: {body.guess!r}"}
        suggestion = _suggest(body.guess, cat)
        if suggestion:
            detail["suggestion"] = suggestion
        raise HTTPException(status_code=400, detail=detail) from None
    except GameAlreadyOverError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None

    state = session.state()
    return {
        "result": result.to_dict(),
        "status": state.status.value,
        "guess_count": state.guess_count,
        "answer_name": state.answer_name,
    }
