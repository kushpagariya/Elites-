"""Small JSON-object SQLite repository. No domain calculations here."""
import json
import os
import sqlite3
import hashlib
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[3] / ".runtime" / "storescout.sqlite3"
current_user: ContextVar[str | None] = ContextVar("storescout_user", default=None)


def base_path():
    return Path(os.getenv("STORESCOUT_DB_PATH", str(DEFAULT_DB)))


class IdempotencyConflict(Exception):
    pass


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@contextmanager
def connection():
    path = base_path()
    user_id = current_user.get()
    if user_id:
        path = path.with_name(f"{path.stem}-{user_id}{path.suffix}")
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    try:
        with db:
            db.execute("CREATE TABLE IF NOT EXISTS objects (kind TEXT, project_id TEXT, object_id TEXT, body TEXT NOT NULL, PRIMARY KEY(kind, project_id, object_id))")
            db.execute("CREATE TABLE IF NOT EXISTS result_cache (project_id TEXT, operation TEXT, cache_key TEXT, object_id TEXT NOT NULL, PRIMARY KEY(project_id, operation, cache_key))")
            db.execute("CREATE TABLE IF NOT EXISTS idempotency (project_id TEXT, operation TEXT, token TEXT, request_hash TEXT NOT NULL, object_id TEXT NOT NULL, PRIMARY KEY(project_id, operation, token))")
            yield db
    finally:
        db.close()


def save(kind: str, project_id: str, object_id: str, body: dict):
    with connection() as db:
        db.execute("INSERT INTO objects VALUES (?, ?, ?, ?)", (kind, project_id, object_id, canonical_json(body)))


def get(kind: str, project_id: str, object_id: str):
    with connection() as db:
        row = db.execute("SELECT body FROM objects WHERE kind=? AND project_id=? AND object_id=?", (kind, project_id, object_id)).fetchone()
    return json.loads(row[0]) if row else None


def list_objects(kind: str, project_id: str):
    with connection() as db:
        rows = db.execute("SELECT body FROM objects WHERE kind=? AND project_id=? ORDER BY object_id", (kind, project_id)).fetchall()
    return [json.loads(row[0]) for row in rows]


def _lookup(db, project_id, operation, cache_key, token, request_hash):
    if token:
        row = db.execute("SELECT request_hash, object_id FROM idempotency WHERE project_id=? AND operation=? AND token=?", (project_id, operation, token)).fetchone()
        if row:
            if row[0] != request_hash:
                raise IdempotencyConflict("Idempotency-Key already belongs to a different request")
            return row[1]
    row = db.execute("SELECT object_id FROM result_cache WHERE project_id=? AND operation=? AND cache_key=?", (project_id, operation, cache_key)).fetchone()
    if row and token:
        db.execute("INSERT INTO idempotency VALUES (?, ?, ?, ?, ?)", (project_id, operation, token, request_hash, row[0]))
    return row[0] if row else None


def cached_id(project_id, operation, cache_key, token, request_hash):
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        return _lookup(db, project_id, operation, cache_key, token, request_hash)


def save_result(project_id, operation, cache_key, token, request_hash, object_id, objects):
    """Atomically publish a result, its private context and cache/token identities.

    Concurrent identical requests use the first committed result. An insert
    failure rolls back every object and index entry in this transaction.
    """
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        existing = _lookup(db, project_id, operation, cache_key, token, request_hash)
        if existing:
            return existing
        for kind, identity, body in objects:
            db.execute("INSERT INTO objects VALUES (?, ?, ?, ?)", (kind, project_id, identity, canonical_json(body)))
        db.execute("INSERT INTO result_cache VALUES (?, ?, ?, ?)", (project_id, operation, cache_key, object_id))
        if token:
            db.execute("INSERT INTO idempotency VALUES (?, ?, ?, ?, ?)", (project_id, operation, token, request_hash, object_id))
    return object_id
