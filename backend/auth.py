"""Accounts: password hashing, signup/login against the `users` table, and sessions.

Password hashes match the seed database: PBKDF2-HMAC-SHA256, 120,000
iterations, stored as `pbkdf2_sha256$<salt>$<hex hash>`, where the salt is
used as UTF-8 text.

Sessions are a signed cookie (`cc_session`) holding the user ID and an expiry
time, signed with HMAC-SHA256 using SESSION_SECRET. Only the backend can create
a valid cookie, and the cookie is HttpOnly so page scripts can't read it.
"""

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
from collections import defaultdict, deque

import db
from models import PublicUser

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 120_000

SESSION_COOKIE = "cc_session"
SESSION_SECONDS = 7 * 24 * 60 * 60  # stay logged in for a week

# Without SESSION_SECRET in .env, a random secret is made at startup, so
# everyone is logged out whenever the backend restarts. Fine for development.
_SECRET = (os.getenv("SESSION_SECRET") or secrets.token_hex(32)).encode()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_MIN = 8
PASSWORD_MAX = 128

# Simple brute-force guard: at most 5 failed logins per email per 15 minutes.
_MAX_FAILURES = 5
_FAILURE_WINDOW = 15 * 60
_failures: dict[str, deque[float]] = defaultdict(deque)


class AuthError(Exception):
    """A signup or login problem that is safe to show the shopper."""

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ---------- Passwords ----------

def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS)
    return f"{ALGORITHM}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, salt, expected = stored.split("$")
    except ValueError:
        return False
    if algorithm != ALGORITHM:
        return False
    actual = hash_password(password, salt).split("$")[2]
    return hmac.compare_digest(actual, expected)


# Checked against when the email is unknown, so a wrong email takes as long as
# a wrong password and response times don't reveal which emails have accounts.
_DUMMY_HASH = hash_password(secrets.token_hex(8))


# ---------- Validation ----------

def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_signup(first_name: str, last_name: str, email: str, password: str) -> None:
    if not first_name.strip() or not last_name.strip():
        raise AuthError("Please enter your first and last name.", 422)
    if not EMAIL_RE.match(email):
        raise AuthError("Please enter a valid email address.", 422)
    if not PASSWORD_MIN <= len(password) <= PASSWORD_MAX:
        raise AuthError(f"Password must be {PASSWORD_MIN}–{PASSWORD_MAX} characters.", 422)


# ---------- Users ----------

def _public(row: sqlite3.Row) -> PublicUser:
    first = row["first_name"] or row["name"].split(" ")[0]
    last = row["last_name"] or " ".join(row["name"].split(" ")[1:])
    return PublicUser(id=row["id"], first_name=first, last_name=last, email=row["email"])


def create_user(first_name: str, last_name: str, email: str, password: str) -> PublicUser:
    first_name, last_name, email = first_name.strip(), last_name.strip(), normalize_email(email)
    validate_signup(first_name, last_name, email, password)
    with db.connect(writable=True) as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, first_name, last_name) "
                "VALUES (?, ?, ?, ?, ?)",
                (f"{first_name} {last_name}", email, hash_password(password), first_name, last_name),
            )
        except sqlite3.IntegrityError:
            raise AuthError("An account with this email already exists. Try logging in.", 409)
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _public(row)


def _too_many_failures(email: str) -> bool:
    attempts = _failures[email]
    cutoff = time.time() - _FAILURE_WINDOW
    while attempts and attempts[0] < cutoff:
        attempts.popleft()
    return len(attempts) >= _MAX_FAILURES


def authenticate(email: str, password: str) -> PublicUser:
    email = normalize_email(email)
    if _too_many_failures(email):
        raise AuthError("Too many failed attempts. Please wait 15 minutes and try again.", 429)
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    stored = row["password_hash"] if row else _DUMMY_HASH
    if not verify_password(password, stored) or row is None:
        _failures[email].append(time.time())
        # Same message for unknown email and wrong password.
        raise AuthError("Incorrect email or password.", 401)
    _failures.pop(email, None)
    return _public(row)


def get_user(user_id: int) -> PublicUser | None:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _public(row) if row else None


# ---------- Session cookie ----------

def _sign(payload: str) -> str:
    return hmac.new(_SECRET, payload.encode(), hashlib.sha256).hexdigest()


def make_session_token(user_id: int) -> str:
    payload = f"{user_id}.{int(time.time()) + SESSION_SECONDS}"
    return f"{payload}.{_sign(payload)}"


def read_session_token(token: str | None) -> int | None:
    """Return the user ID from a valid, unexpired token, else None."""
    if not token:
        return None
    try:
        user_id, expires, signature = token.split(".")
        payload = f"{user_id}.{expires}"
        if not hmac.compare_digest(signature, _sign(payload)) or int(expires) < time.time():
            return None
        return int(user_id)
    except ValueError:
        return None
