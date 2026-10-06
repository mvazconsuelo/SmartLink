"""Data access to Cloudflare D1.

SmartLink runs outside Cloudflare Workers, so it cannot use a D1 binding.
It talks to D1 through the Cloudflare REST API:

    POST /client/v4/accounts/{account_id}/d1/database/{database_id}/query

Every SQL statement in the application goes through the `Database` interface
defined here. The rest of the code never knows whether it is talking to D1 or
to the in-memory fake used by the tests.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx

logger = logging.getLogger("smartlink.database")

D1_API_BASE = "https://api.cloudflare.com/client/v4"

# All timestamps are stored as UTC text in this format (see migrations/001).
DB_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class DatabaseError(Exception):
    """Base class for every database failure."""


class DatabaseUnavailable(DatabaseError):
    """D1 could not be reached or did not answer: timeout, network, 5xx, auth.

    Maps to HTTP 503. The request was fine; the dependency is not.
    """


class QueryError(DatabaseError):
    """D1 answered but rejected the statement (bad SQL, missing column...).

    Maps to HTTP 500. Usually a bug or an app/schema version mismatch.
    """


class UniqueViolation(QueryError):
    """A UNIQUE constraint failed (duplicate username or short code)."""


@dataclass
class QueryResult:
    """The rows and metadata of one statement."""

    rows: list[dict[str, Any]] = field(default_factory=list)
    changes: int = 0
    last_row_id: int | None = None


Statement = tuple[str, Sequence[Any]]


class Database(Protocol):
    """What the app needs from a database. D1Database implements it; the tests use an in-memory fake."""

    def query(self, sql: str, params: Sequence[Any] = ()) -> QueryResult:
        """Run one SQL statement."""
        ...

    def batch(self, statements: list[Statement]) -> list[QueryResult]:
        """Run several statements in one request."""
        ...

    def close(self) -> None:
        """Release the connection."""
        ...


def utcnow() -> datetime:
    """The current UTC time, without microseconds."""
    return datetime.now(UTC).replace(microsecond=0)


def to_db_time(value: datetime) -> str:
    """A datetime as the UTC text stored in D1."""
    return value.astimezone(UTC).strftime(DB_TIME_FORMAT)


def from_db_time(value: str | None) -> datetime | None:
    """The inverse of to_db_time. None stays None."""
    if value is None:
        return None
    return datetime.strptime(value, DB_TIME_FORMAT).replace(tzinfo=UTC)


def raise_for_sql_error(message: str) -> None:
    """Raise UniqueViolation for a UNIQUE failure, QueryError for anything else."""
    if "UNIQUE constraint failed" in message:
        raise UniqueViolation(message)
    raise QueryError(message)


class D1Database:
    """Cloudflare D1 accessed over its REST API."""

    def __init__(
        self,
        account_id: str,
        database_id: str,
        api_token: str,
        timeout_seconds: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=f"{D1_API_BASE}/accounts/{account_id}/d1/database/{database_id}",
            headers={"Authorization": f"Bearer {api_token}"},
            timeout=timeout_seconds,
            transport=transport,
        )

    def query(self, sql: str, params: Sequence[Any] = ()) -> QueryResult:
        """Run one SQL statement."""
        return self._post({"sql": sql, "params": list(params)})[0]

    def batch(self, statements: list[Statement]) -> list[QueryResult]:
        """Run several statements in one request."""
        body = {"batch": [{"sql": sql, "params": list(params)} for sql, params in statements]}
        return self._post(body)

    def close(self) -> None:
        """Close the HTTP connection."""
        self._client.close()

    def _post(self, body: dict[str, Any]) -> list[QueryResult]:
        started = time.perf_counter()
        try:
            response = self._client.post("/query", json=body)
        except httpx.TimeoutException as exc:
            logger.error("d1 request failed reason=timeout error=%r", str(exc))
            raise DatabaseUnavailable("D1 request timed out") from exc
        except httpx.HTTPError as exc:
            logger.error("d1 request failed reason=connection error=%r", str(exc))
            raise DatabaseUnavailable("D1 connection error") from exc

        duration_ms = round((time.perf_counter() - started) * 1000)
        status = response.status_code

        if status in (401, 403):
            # Never log the token; the status code is enough to diagnose it.
            logger.error("d1 request failed reason=auth status=%s duration_ms=%s", status, duration_ms)
            raise DatabaseUnavailable("D1 rejected the API token")
        if status == 429 or status >= 500:
            logger.error("d1 request failed reason=upstream status=%s duration_ms=%s", status, duration_ms)
            raise DatabaseUnavailable(f"D1 returned HTTP {status}")

        try:
            payload = response.json()
        except ValueError as exc:
            logger.error("d1 request failed reason=invalid_json status=%s", status)
            raise DatabaseUnavailable("D1 returned a non-JSON response") from exc

        if not payload.get("success", False):
            message = "; ".join(e.get("message", "") for e in payload.get("errors", [])) or "unknown D1 error"
            logger.error("d1 query rejected status=%s error=%r", status, message)
            raise_for_sql_error(message)

        logger.debug("d1 query ok duration_ms=%s", duration_ms)
        results = []
        for item in payload.get("result", []):
            meta = item.get("meta") or {}
            results.append(
                QueryResult(
                    rows=item.get("results") or [],
                    changes=meta.get("changes", 0),
                    last_row_id=meta.get("last_row_id"),
                )
            )
        return results
