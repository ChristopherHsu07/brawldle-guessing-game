"""FastAPI REST layer for Brawldle.

Run from the backend/ directory:
  uvicorn src.api:app --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import logging
import difflib
import uuid
import os

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field

from src.catalog import BrawlerCatalog
from src.session import GameAlreadyOverError, GameSession, InvalidGuessError

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import redis.asyncio as redis
import json
from src.compare import compare_guess
from src.models import GameStatus, GuessResult

logger = logging.getLogger("uvicorn.error")

SESSION_COOKIE = "brawldle_session"
SESSION_COOKIE_MAX_AGE = 24 * 60 * 60  # 24 hours
SESSION_TTL_SECONDS = SESSION_COOKIE_MAX_AGE  # keep server TTL in sync with the cookie
REDIS_SOCKET_TIMEOUT_SECONDS = 3

REDIS_URL = os.environ.get("REDIS_URL") or None
redis_client: redis.Redis | None = None
sessions: dict[str, GameSession] = {}
catalog: BrawlerCatalog | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global catalog, redis_client
    logger.info("Loading brawler catalog")
    catalog = BrawlerCatalog()
    logger.info("Catalog loaded (%s brawlers)", len(catalog))
    if REDIS_URL:
        logger.info("Using Redis at %s", REDIS_URL)
        redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=REDIS_SOCKET_TIMEOUT_SECONDS,
            socket_timeout=REDIS_SOCKET_TIMEOUT_SECONDS,
        )
    else:
        logger.info("REDIS_URL unset; using in-memory sessions")
        redis_client = None
    yield
    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None
    sessions.clear()
    catalog = None

app = FastAPI(
    title="Brawldle",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,  # also hides /openapi.json, the underlying schema
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_is_production = os.environ.get("ENVIRONMENT", "development") == "production"

class GuessRequest(BaseModel):
    guess: str = Field(min_length=1, max_length=20)


def _require_catalog() -> BrawlerCatalog:
    if catalog is None:
        raise HTTPException(status_code=503, detail="Catalog not loaded.")
    return catalog


def _serialize_session(session: GameSession) -> str:
    return json.dumps({
        "answer_name": session.answer.name,
        "guess_names": [g.guess_name for g in session.history],
        "status": session.status.value,
    })

def _deserialize_session(data: str, cat: BrawlerCatalog) -> GameSession:
    payload = json.loads(data)
    answer = cat.get_by_name(payload["answer_name"])
    history = [
        GuessResult(
            guess_name=name,
            attributes=compare_guess(cat.get_by_name(name), answer),
            correct=name.casefold() == answer.name.casefold(),
        )
        for name in payload["guess_names"]
    ]
    return GameSession(
        catalog=cat,
        answer=answer,
        history=history,
        status=GameStatus(payload["status"]),
    )


async def _save_session(session_id: str, session: GameSession) -> None:
    if redis_client is not None:
        await redis_client.set(
            f"session:{session_id}",
            _serialize_session(session),
            ex=SESSION_TTL_SECONDS,
        )
        return
    sessions[session_id] = session


async def _try_get_session(session_id: str, cat: BrawlerCatalog) -> GameSession | None:
    if redis_client is not None:
        data = await redis_client.get(f"session:{session_id}")
        if data is None:
            return None
        return _deserialize_session(data, cat)
    return sessions.get(session_id)


async def _get_session(session_id: str, cat: BrawlerCatalog) -> GameSession:
    session = await _try_get_session(session_id, cat)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session_id.")
    return session

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
        secure=_is_production,
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
async def home(request: Request, response: Response) -> dict[str, Any]:
    cat = _require_catalog()
    cookie_id = request.cookies.get(SESSION_COOKIE)
    if cookie_id:
        session = await _try_get_session(cookie_id, cat)
        if session is not None:
            return _game_payload(cookie_id, session, cat)
 
    session = GameSession.new(cat)
    session_id = str(uuid.uuid4())
    await _save_session(session_id, session)
    _set_session_cookie(response, session_id)
    return _game_payload(session_id, session, cat)


@app.post("/new")
@limiter.limit("30/minute")
async def new_game(request: Request) -> dict[str, Any]:
    """Start a fresh round under the existing session cookie (no new cookie)."""
    cat = _require_catalog()
    session_id = request.cookies.get(SESSION_COOKIE)
    session = GameSession.new(cat)
    if not session_id:
        raise HTTPException(status_code=404, detail="Unknown session_id.")
    await _save_session(session_id, session)
    return _game_payload(session_id, session, cat)

@app.post("/guess")
@limiter.limit("20/minute")
async def submit_guess(request: Request, body: GuessRequest) -> dict[str, Any]:
    cat = _require_catalog()
    session_id = request.cookies.get(SESSION_COOKIE)
    if not session_id:
        raise HTTPException(status_code=404, detail="Unknown session_id.")
    session = await _get_session(session_id, cat)

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

    await _save_session(session_id, session)

    state = session.state()
    return {
        "result": result.to_dict(),
        "status": state.status.value,
        "guess_count": state.guess_count,
        "answer_name": state.answer_name,
    }

@app.get("/health")
@app.head("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}