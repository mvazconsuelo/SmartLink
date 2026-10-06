"""Test fixtures.

Tests never touch Cloudflare. They use FakeD1, an in-memory SQLite database
behind the same `Database` interface as D1Database. D1 is built on SQLite, so
the fake runs the real SQL of the application against the real schema from
migrations/. It exists only in tests; the running app always uses D1.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app import auth
from app.config import Settings
from app.database import DatabaseUnavailable, QueryError, QueryResult, Statement, raise_for_sql_error
from app.main import create_app

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


class FakeD1:
    def __init__(self) -> None:
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
            self._conn.executescript(migration.read_text())

    def _execute(self, sql: str, params: Sequence[Any]) -> QueryResult:
        try:
            cursor = self._conn.execute(sql, list(params))
        except sqlite3.Error as exc:
            raise_for_sql_error(str(exc))
        rows = [dict(row) for row in cursor.fetchall()]
        return QueryResult(rows=rows, changes=max(cursor.rowcount, 0), last_row_id=cursor.lastrowid)

    def query(self, sql: str, params: Sequence[Any] = ()) -> QueryResult:
        with self._lock, self._conn:
            return self._execute(sql, params)

    def batch(self, statements: list[Statement]) -> list[QueryResult]:
        with self._lock, self._conn:
            return [self._execute(sql, params) for sql, params in statements]

    def close(self) -> None:
        self._conn.close()


class BrokenD1:
    """Simulates D1 being unreachable (timeout, network, bad token)."""

    def query(self, sql: str, params: Sequence[Any] = ()) -> QueryResult:
        raise DatabaseUnavailable("simulated outage")

    def batch(self, statements: list[Statement]) -> list[QueryResult]:
        raise DatabaseUnavailable("simulated outage")

    def close(self) -> None:
        pass


TEST_SETTINGS = Settings(jwt_secret="test-secret-not-for-production-0123456789", public_base_url="http://sl.test")


@pytest.fixture(autouse=True)
def fast_password_hashing(monkeypatch):
    monkeypatch.setattr(auth, "PBKDF2_ITERATIONS", 1_000)


@pytest.fixture
def db() -> FakeD1:
    return FakeD1()


@pytest.fixture
def client(db) -> TestClient:
    with TestClient(create_app(TEST_SETTINGS, db=db), follow_redirects=False) as test_client:
        yield test_client


def register(client: TestClient, username: str = "alice", password: str = "correct-horse") -> dict[str, str]:
    response = client.post("/auth/register", json={"username": username, "password": password})
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def auth_headers(client) -> dict[str, str]:
    return register(client)


__all__ = ["TEST_SETTINGS", "BrokenD1", "FakeD1", "QueryError", "register"]
