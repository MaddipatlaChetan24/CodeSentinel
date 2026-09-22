"""Minimal SQLite-backed history store for reviews run through the dashboard."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from codesentinel.review.models import ReviewResult

DB_PATH = Path.home() / ".codesentinel" / "history.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target TEXT NOT NULL,
    language TEXT NOT NULL,
    score INTEGER NOT NULL,
    verdict TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at REAL NOT NULL
);
"""


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_SCHEMA)
    return conn


def save_review(result: ReviewResult) -> int:
    conn = _connect()
    with conn:
        cur = conn.execute(
            "INSERT INTO reviews (target, language, score, verdict, result_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                result.target,
                result.language,
                result.score,
                result.verdict,
                json.dumps(result.to_dict()),
                time.time(),
            ),
        )
        return cur.lastrowid


def list_reviews(limit: int = 50) -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        "SELECT id, target, language, score, verdict, created_at FROM reviews "
        "ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [
        {
            "id": r[0],
            "target": r[1],
            "language": r[2],
            "score": r[3],
            "verdict": r[4],
            "created_at": r[5],
        }
        for r in rows
    ]


def get_review(review_id: int) -> dict | None:
    conn = _connect()
    row = conn.execute(
        "SELECT result_json FROM reviews WHERE id = ?", (review_id,)
    ).fetchone()
    return json.loads(row[0]) if row else None
