"""FastAPI REST layer for Brawldle.

Run the server with:
  uvicorn src.api:app --reload
"""

from __future__ import annotations

import difflib
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.catalog import BrawlerCatalog
from src.session import GameAlreadyOverError, GameSession, InvalidGuessError

sessions: dict[str, GameSession] = {}
catalog: BrawlerCatalog | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global catalog
    catalog = BrawlerCatalog()
    yield
    sessions.clear()
    catalog = None


app = FastAPI(title="Brawldle", lifespan=lifespan)


class GuessRequest(BaseModel):
    session_id: str
    guess: str = Field(min_length=1)


def _require_catalog() -> BrawlerCatalog:
    if catalog is None:
        raise HTTPException(status_code=503, detail="Catalog not loaded.")
    return catalog


def _get_session(session_id: str) -> GameSession:
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session_id.")
    return session


def _suggest(name: str, cat: BrawlerCatalog) -> str | None:
    matches = difflib.get_close_matches(
        name.strip(), cat.all_names(), n=1, cutoff=0.6
    )
    return matches[0] if matches else None


@app.get("/")
def home() -> dict[str, Any]:
    cat = _require_catalog()
    session = GameSession.new(cat)
    session_id = str(uuid.uuid4())
    sessions[session_id] = session
    return {
        "session_id": session_id,
        "brawler_count": len(cat),
        "state": session.to_dict(),
    }


@app.post("/guess")
def submit_guess(body: GuessRequest) -> dict[str, Any]:
    cat = _require_catalog()
    session = _get_session(body.session_id)

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

    return {
        "result": result.to_dict(),
        "state": session.to_dict(),
    }
