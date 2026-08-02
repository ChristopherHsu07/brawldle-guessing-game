"""Brawldle entry points.

CLI (default):
  python main.py

REST API:
  uvicorn src.api:app --reload
  Then open http://127.0.0.1:8000/docs for interactive docs.
"""

from src.cli import run


if __name__ == "__main__":
    run()
