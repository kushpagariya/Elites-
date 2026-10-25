"""Local email/password accounts, revocable sessions, and isolated workspaces."""
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager, closing

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field, field_validator

from .repositories import store
from .services.errors import ServiceError

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
COOKIE = "storescout_session"
LIFETIME = 60 * 60 * 24 * 7


@contextmanager
def database():
    path = store.base_path().with_name("accounts.sqlite3")
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, timeout=10)) as db:
        db.row_factory = sqlite3.Row
        db.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, salt TEXT NOT NULL, password_hash TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires INTEGER NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS attempts (key TEXT PRIMARY KEY, count INTEGER NOT NULL, expires INTEGER NOT NULL)")
        try:
            yield db
        finally:
            db.commit()


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def email_address(cls, value):
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address.")
        return value


class Registration(Credentials):
    name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("name")
    @classmethod
    def display_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Enter your name.")
        return value


def password_hash(password, salt):
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1, dklen=32).hex()


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def public_user(row):
    return {key: row[key] for key in ("id", "name", "email")}


def session_user(token):
    if not token or len(token) > 128:
        return None
    with database() as db:
        row = db.execute("SELECT users.* FROM users JOIN sessions ON users.id=sessions.user_id WHERE token_hash=? AND expires>?", (token_hash(token), int(time.time()))).fetchone()
    return public_user(row) if row else None


def throttle(request, email):
    now = int(time.time())
    address = request.client.host if request.client else "local"
    with database() as db:
        db.execute("DELETE FROM attempts WHERE expires<=?", (now,))
        for key, limit in (("ip:" + address, 40), ("email:" + email, 10)):
            key = token_hash(key)
            db.execute("INSERT INTO attempts VALUES (?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1", (key, now + 900))
            if db.execute("SELECT count FROM attempts WHERE key=?", (key,)).fetchone()[0] > limit:
                raise ServiceError(429, "TOO_MANY_ATTEMPTS", "Too many sign-in attempts. Please try again in 15 minutes.")


def issue_session(request, response, user_id):
    token = secrets.token_urlsafe(32)
    now = int(time.time())
    with database() as db:
        db.execute("DELETE FROM sessions WHERE expires<=?", (now,))
        old = request.cookies.get(COOKIE)
        if old:
            db.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash(old),))
        db.execute("INSERT INTO sessions VALUES (?,?,?)", (token_hash(token), user_id, now + LIFETIME))
    response.set_cookie(COOKIE, token, max_age=LIFETIME, httponly=True, samesite="lax", secure=os.getenv("STORESCOUT_SECURE_COOKIES") == "1", path="/")
    response.headers["Cache-Control"] = "no-store"


@router.post("/register", status_code=201)
def register(body: Registration, request: Request, response: Response):
    throttle(request, body.email)
    salt = secrets.token_hex(16)
    user = {"id": secrets.token_hex(16), "name": body.name, "email": body.email}
    hashed = password_hash(body.password, salt)
    try:
        with database() as db:
            db.execute("INSERT INTO users VALUES (?,?,?,?,?)", (user["id"], user["name"], user["email"], salt, hashed))
    except sqlite3.IntegrityError:
        raise ServiceError(409, "ACCOUNT_EXISTS", "An account already uses this email. Please sign in.")
    issue_session(request, response, user["id"])
    return {"data": user}


@router.post("/login")
def login(body: Credentials, request: Request, response: Response):
    throttle(request, body.email)
    with database() as db:
        user = db.execute("SELECT * FROM users WHERE email=?", (body.email,)).fetchone()
    # Keep the costly password check for unknown accounts too.
    hashed = password_hash(body.password, user["salt"] if user else "00" * 16)
    if not user or not hmac.compare_digest(hashed, user["password_hash"]):
        raise ServiceError(401, "INVALID_CREDENTIALS", "Email or password is incorrect.")
    issue_session(request, response, user["id"])
    return {"data": public_user(user)}


@router.get("/me")
def me(request: Request, response: Response):
    user = session_user(request.cookies.get(COOKIE))
    if not user:
        raise ServiceError(401, "SIGN_IN_REQUIRED", "Please sign in to continue.")
    response.headers["Cache-Control"] = "no-store"
    return {"data": user}


@router.post("/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(COOKIE)
    if token:
        with database() as db:
            db.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash(token),))
    response.delete_cookie(COOKIE, path="/")
    response.headers["Cache-Control"] = "no-store"
    return {"data": {"signed_out": True}}
