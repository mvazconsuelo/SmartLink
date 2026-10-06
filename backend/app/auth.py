"""Small, educational authentication: username + password, stateless JWT.

- Passwords are hashed with PBKDF2-HMAC-SHA256 (Python standard library),
  with a random salt per user.
- Login returns a signed JWT (HS256). The API trusts the token's signature and
  expiry without hitting D1 on every request.
- Trade-off: a token cannot be revoked before it expires. A real Identity
  Provider (OIDC) would replace create_user/authenticate/create_access_token,
  and the API would only validate the IdP's tokens in get_current_user.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import timedelta

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .database import Database, UniqueViolation, to_db_time, utcnow

PBKDF2_ITERATIONS = 600_000
JWT_ALGORITHM = "HS256"


class UsernameTaken(Exception):
    """The username already exists."""


@dataclass(frozen=True)
class CurrentUser:
    """The authenticated user, as read from a valid token."""

    id: int
    username: str


def hash_password(password: str) -> str:
    """Hash with PBKDF2-HMAC-SHA256 and a random salt: pbkdf2_sha256$iterations$salt$digest."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    """Check a password against a stored hash in constant time. False if the hash is malformed."""
    try:
        algorithm, iterations, salt_b64, digest_b64 = stored.split("$")
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt_b64), int(iterations))
    return hmac.compare_digest(digest, base64.b64decode(digest_b64))


# Used when the username does not exist, so a failed login takes the same time
# whether or not the user exists (avoids user enumeration by timing).
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def create_user(db: Database, username: str, password: str) -> CurrentUser:
    """Insert a user. Raises UsernameTaken if the name exists."""
    try:
        result = db.query(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            [username, hash_password(password), to_db_time(utcnow())],
        )
    except UniqueViolation as exc:
        raise UsernameTaken(username) from exc
    return CurrentUser(id=result.last_row_id, username=username)


def authenticate(db: Database, username: str, password: str) -> CurrentUser | None:
    """Return the user if the credentials match, else None. Takes the same time either way."""
    rows = db.query("SELECT id, username, password_hash FROM users WHERE username = ?", [username]).rows
    if not rows:
        verify_password(password, _DUMMY_HASH)
        return None
    user = rows[0]
    if not verify_password(password, user["password_hash"]):
        return None
    return CurrentUser(id=user["id"], username=user["username"])


def create_access_token(user: CurrentUser, secret: str, ttl_minutes: int) -> str:
    """Sign a JWT (HS256) with the user's id and name, valid for ttl_minutes."""
    now = utcnow()
    claims = {
        "sub": str(user.id),
        "username": user.username,
        "iat": now,
        "exp": now + timedelta(minutes=ttl_minutes),
    }
    return jwt.encode(claims, secret, algorithm=JWT_ALGORITHM)


_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    """FastAPI dependency: the user in the Bearer token, or 401. Never queries D1."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        claims = jwt.decode(
            credentials.credentials,
            request.app.state.settings.jwt_secret,
            algorithms=[JWT_ALGORITHM],
        )
        return CurrentUser(id=int(claims["sub"]), username=claims["username"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise unauthorized from None
