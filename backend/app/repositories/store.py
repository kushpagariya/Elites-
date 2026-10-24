"""Small JSON-object SQLite repository. No domain calculations here."""
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[3] / ".runtime" / "storescout.sqlite3"


@contextmanager
def connection():
    path = Path(os.getenv("STORESCOUT_DB_PATH", str(DEFAULT_DB)))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    try:
        with db:
            db.execute("CREATE TABLE IF NOT EXISTS objects (kind TEXT, project_id TEXT, object_id TEXT, body TEXT NOT NULL, PRIMARY KEY(kind, project_id, object_id))")
            yield db
    finally:
        db.close()


def save(kind: str, project_id: str, object_id: str, body: dict):
    with connection() as db:
        db.execute("INSERT INTO objects VALUES (?, ?, ?, ?)", (kind, project_id, object_id, json.dumps(body, allow_nan=False)))


def get(kind: str, project_id: str, object_id: str):
    with connection() as db:
        row = db.execute("SELECT body FROM objects WHERE kind=? AND project_id=? AND object_id=?", (kind, project_id, object_id)).fetchone()
    return json.loads(row[0]) if row else None


def list_objects(kind: str, project_id: str):
    with connection() as db:
        rows = db.execute("SELECT body FROM objects WHERE kind=? AND project_id=? ORDER BY object_id", (kind, project_id)).fetchall()
    return [json.loads(row[0]) for row in rows]


def save_many(project_id: str, objects: list[tuple[str, str, dict]]):
    """Commit public output, private snapshot and cache/idempotency records atomically."""
    with connection() as db:
        for kind, object_id, body in objects:
            db.execute("INSERT INTO objects VALUES (?, ?, ?, ?)",
                       (kind, project_id, object_id, json.dumps(body, allow_nan=False)))
