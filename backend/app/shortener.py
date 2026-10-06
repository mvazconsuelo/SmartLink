"""Short URL business logic: create, look up, resolve, status."""

from __future__ import annotations

import logging
import re
import secrets
import string
from datetime import datetime
from typing import Any

from .database import Database, UniqueViolation, from_db_time, to_db_time, utcnow

logger = logging.getLogger("smartlink.shortener")

CODE_ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 7
ALIAS_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,32}$")

# Paths an alias must never shadow: the API's own routes, plus "app", which
# the Ingress sends to the Streamlit dashboard (deploy/components/smartlink-frontend/templates/ingress.yaml).
RESERVED_CODES = {"app", "auth", "docs", "health", "openapi.json", "redoc", "shorten", "stats", "urls"}

_URL_COLUMNS = "id, user_id, code, original_url, created_at, expires_at, is_active, click_count"


class InvalidAlias(Exception):
    """The alias is malformed or reserved."""


class AliasTaken(Exception):
    """The alias is already used by another link."""


class InvalidExpiration(Exception):
    """The expiration is not in the future."""


class LinkNotFound(Exception):
    """No link with that code, or it is not yours."""


class LinkExpired(Exception):
    """The link exists but its expiration has passed."""


def generate_code() -> str:
    """A random 7-character code (62^7 possibilities)."""
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def link_status(row: dict[str, Any], now: datetime | None = None) -> str:
    """'active', 'expired' or 'inactive'."""
    if not row["is_active"]:
        return "inactive"
    expires_at = from_db_time(row["expires_at"])
    if expires_at is not None and expires_at <= (now or utcnow()):
        return "expired"
    return "active"


def create_short_url(
    db: Database,
    user_id: int,
    original_url: str,
    custom_alias: str | None = None,
    expires_at: datetime | None = None,
) -> dict[str, Any]:
    """Create a link (random code, or the given alias) and return its row."""
    now = utcnow()
    if expires_at is not None and expires_at <= now:
        raise InvalidExpiration("expires_at must be in the future")

    if custom_alias:
        if not ALIAS_PATTERN.match(custom_alias) or custom_alias.lower() in RESERVED_CODES:
            raise InvalidAlias(custom_alias)
        candidates = [custom_alias]
    else:
        # 62^7 possible codes: a collision is very unlikely, but cheap to retry.
        candidates = [generate_code() for _ in range(3)]

    for code in candidates:
        try:
            db.query(
                "INSERT INTO short_urls (user_id, code, original_url, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
                [user_id, code, original_url, to_db_time(now), to_db_time(expires_at) if expires_at else None],
            )
        except UniqueViolation:
            if custom_alias:
                raise AliasTaken(custom_alias) from None
            logger.warning("generated code collision code=%s", code)
            continue
        logger.info("short url created code=%s user_id=%s custom_alias=%s", code, user_id, bool(custom_alias))
        return get_by_code(db, code)

    raise RuntimeError("could not generate a unique short code")


def get_by_code(db: Database, code: str) -> dict[str, Any]:
    """The row for a code. Raises LinkNotFound."""
    rows = db.query(f"SELECT {_URL_COLUMNS} FROM short_urls WHERE code = ?", [code]).rows
    if not rows:
        raise LinkNotFound(code)
    return rows[0]


def get_user_url(db: Database, user_id: int, code: str) -> dict[str, Any]:
    """Like get_by_code, but only for the owner: someone else's link is 'not found'."""
    row = get_by_code(db, code)
    # Someone else's link is reported as "not found", not "forbidden",
    # so the API does not reveal which codes exist.
    if row["user_id"] != user_id:
        raise LinkNotFound(code)
    return row


def list_user_urls(db: Database, user_id: int) -> list[dict[str, Any]]:
    """All of a user's links, newest first."""
    return db.query(
        f"SELECT {_URL_COLUMNS} FROM short_urls WHERE user_id = ? ORDER BY created_at DESC, id DESC",
        [user_id],
    ).rows


def resolve(db: Database, code: str) -> dict[str, Any]:
    """Return the link for a redirect, or raise LinkNotFound / LinkExpired."""
    row = get_by_code(db, code)
    status = link_status(row)
    if status == "inactive":
        raise LinkNotFound(code)
    if status == "expired":
        raise LinkExpired(code)
    return row
