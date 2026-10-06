"""D1Database against a mocked Cloudflare API (no network)."""

import json

import httpx
import pytest

from app.database import D1Database, DatabaseUnavailable, QueryError, UniqueViolation


def make_db(handler) -> D1Database:
    return D1Database("acc", "db-id", "secret-token", transport=httpx.MockTransport(handler))


def ok(results, last_row_id=None):
    return httpx.Response(
        200,
        json={
            "success": True,
            "errors": [],
            "messages": [],
            "result": [{"success": True, "results": results, "meta": {"changes": 1, "last_row_id": last_row_id}}],
        },
    )


def test_query_sends_sql_params_and_token():
    seen = {}

    def handler(request: httpx.Request):
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return ok([{"id": 1}], last_row_id=1)

    result = make_db(handler).query("SELECT id FROM users WHERE username = ?", ["alice"])

    assert seen["url"] == "https://api.cloudflare.com/client/v4/accounts/acc/d1/database/db-id/query"
    assert seen["auth"] == "Bearer secret-token"
    assert seen["body"] == {"sql": "SELECT id FROM users WHERE username = ?", "params": ["alice"]}
    assert result.rows == [{"id": 1}]
    assert result.last_row_id == 1


def test_batch_body():
    seen = {}

    def handler(request):
        seen["body"] = json.loads(request.content)
        return ok([])

    make_db(handler).batch([("SELECT 1", []), ("SELECT ?", [2])])
    assert seen["body"] == {"batch": [{"sql": "SELECT 1", "params": []}, {"sql": "SELECT ?", "params": [2]}]}


def test_timeout_is_unavailable():
    def handler(request):
        raise httpx.ReadTimeout("timed out", request=request)

    with pytest.raises(DatabaseUnavailable):
        make_db(handler).query("SELECT 1")


@pytest.mark.parametrize("status", [401, 403, 429, 500, 503])
def test_upstream_errors_are_unavailable(status):
    with pytest.raises(DatabaseUnavailable):
        make_db(lambda request: httpx.Response(status, json={"success": False})).query("SELECT 1")


def test_sql_error_is_query_error():
    response = httpx.Response(400, json={"success": False, "errors": [{"code": 7500, "message": "no such column: x"}]})
    with pytest.raises(QueryError):
        make_db(lambda request: response).query("SELECT x")


def test_unique_violation():
    response = httpx.Response(
        400, json={"success": False, "errors": [{"code": 7500, "message": "UNIQUE constraint failed: users.username"}]}
    )
    with pytest.raises(UniqueViolation):
        make_db(lambda request: response).query("INSERT ...")


def test_token_never_logged(caplog):
    with pytest.raises(DatabaseUnavailable):
        make_db(lambda request: httpx.Response(403, json={"success": False})).query("SELECT 1")
    assert "secret-token" not in caplog.text
