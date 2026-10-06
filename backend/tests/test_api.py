from datetime import timedelta

from fastapi.testclient import TestClient

from app.database import to_db_time, utcnow
from app.main import create_app

from .conftest import TEST_SETTINGS, BrokenD1, register


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


# --- auth -------------------------------------------------------------------


def test_register_and_login(client):
    register(client, "bob", "password123")
    response = client.post("/auth/login", json={"username": "bob", "password": "password123"})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_wrong_password(client):
    register(client, "bob", "password123")
    response = client.post("/auth/login", json={"username": "bob", "password": "wrong-password"})
    assert response.status_code == 401


def test_duplicate_username(client):
    register(client, "bob")
    response = client.post("/auth/register", json={"username": "bob", "password": "other-password"})
    assert response.status_code == 409


def test_endpoints_require_token(client):
    assert client.get("/urls").status_code == 401
    assert client.post("/shorten", json={"original_url": "https://example.com"}).status_code == 401
    assert client.get("/urls", headers={"Authorization": "Bearer not-a-jwt"}).status_code == 401


def test_password_is_not_stored_in_plain_text(client, db):
    register(client, "bob", "password123")
    stored = db.query("SELECT password_hash FROM users WHERE username = 'bob'").rows[0]["password_hash"]
    assert "password123" not in stored
    assert stored.startswith("pbkdf2_sha256$")


# --- shorten ----------------------------------------------------------------


def test_shorten_generates_code(client, auth_headers):
    response = client.post("/shorten", json={"original_url": "https://example.com/page"}, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert len(body["code"]) == 7
    assert body["short_url"] == f"http://sl.test/{body['code']}"
    assert body["status"] == "active"
    assert body["expires_at"] is None


def test_shorten_with_custom_alias(client, auth_headers):
    response = client.post(
        "/shorten", json={"original_url": "https://example.com", "custom_alias": "manual"}, headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["code"] == "manual"


def test_alias_already_taken(client, auth_headers):
    payload = {"original_url": "https://example.com", "custom_alias": "manual"}
    client.post("/shorten", json=payload, headers=auth_headers)
    assert client.post("/shorten", json=payload, headers=auth_headers).status_code == 409


def test_reserved_or_invalid_alias(client, auth_headers):
    for alias in ["health", "urls", "app", "a", "with space", "x" * 40]:
        response = client.post(
            "/shorten", json={"original_url": "https://example.com", "custom_alias": alias}, headers=auth_headers
        )
        assert response.status_code == 422, alias


def test_rejects_non_http_urls(client, auth_headers):
    response = client.post("/shorten", json={"original_url": "javascript:alert(1)"}, headers=auth_headers)
    assert response.status_code == 422


def test_expiration_date_means_end_of_that_day(client, auth_headers):
    response = client.post(
        "/shorten", json={"original_url": "https://example.com", "expires_at": "2099-12-31"}, headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["expires_at"].startswith("2100-01-01T00:00:00")


def test_expiration_in_the_past_is_rejected(client, auth_headers):
    response = client.post(
        "/shorten", json={"original_url": "https://example.com", "expires_at": "2000-01-01"}, headers=auth_headers
    )
    assert response.status_code == 422


# --- redirect ---------------------------------------------------------------


def test_redirect_and_click_recorded(client, auth_headers, db):
    client.post("/shorten", json={"original_url": "https://example.com", "custom_alias": "gol"}, headers=auth_headers)

    response = client.get("/gol", headers={"Referer": "https://news.example.org/some/path?user=42"})
    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/"

    detail = client.get("/urls/gol", headers=auth_headers).json()
    assert detail["click_count"] == 1
    assert detail["recent_clicks"][0]["referrer"] == "news.example.org"  # host only, no path/query
    assert detail["clicks_per_day"][0]["clicks"] == 1


def test_redirect_unknown_code(client):
    assert client.get("/nope123").status_code == 404


def test_expired_link_returns_410(client, auth_headers, db):
    client.post("/shorten", json={"original_url": "https://example.com", "custom_alias": "old"}, headers=auth_headers)
    # Force expiration in the past directly in the database.
    yesterday = to_db_time(utcnow() - timedelta(days=1))
    db.query("UPDATE short_urls SET expires_at = ? WHERE code = 'old'", [yesterday])

    assert client.get("/old").status_code == 410
    assert client.get("/urls/old", headers=auth_headers).json()["status"] == "expired"


def test_redirect_still_works_if_click_recording_fails(client, auth_headers, db):
    client.post("/shorten", json={"original_url": "https://example.com", "custom_alias": "gol"}, headers=auth_headers)
    db.query("DROP TABLE click_events")  # simulate app/schema mismatch

    assert client.get("/gol").status_code == 302


# --- per-user isolation -------------------------------------------------------


def test_users_only_see_their_own_links(client):
    alice = register(client, "alice")
    bob = register(client, "bob")
    client.post("/shorten", json={"original_url": "https://alice.example", "custom_alias": "alice1"}, headers=alice)

    assert [u["code"] for u in client.get("/urls", headers=alice).json()] == ["alice1"]
    assert client.get("/urls", headers=bob).json() == []
    assert client.get("/urls/alice1", headers=bob).status_code == 404
    assert client.get("/urls/alice1/qr", headers=bob).status_code == 404


# --- QR and dashboard -------------------------------------------------------


def test_qr_png(client, auth_headers):
    client.post("/shorten", json={"original_url": "https://example.com", "custom_alias": "qr1"}, headers=auth_headers)
    response = client.get("/urls/qr1/qr", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


def test_dashboard(client, auth_headers, db):
    for alias in ["one", "two"]:
        payload = {"original_url": "https://example.com", "custom_alias": alias}
        client.post("/shorten", json=payload, headers=auth_headers)
    client.get("/one")
    client.get("/one")
    client.get("/two")
    db.query("UPDATE short_urls SET expires_at = ? WHERE code = 'two'", [to_db_time(utcnow() - timedelta(hours=1))])

    stats = client.get("/stats", headers=auth_headers).json()
    assert stats["total_urls"] == 2
    assert stats["total_clicks"] == 3
    assert stats["expired_urls"] == 1
    assert stats["top_links"][0]["code"] == "one"
    assert sum(day["clicks"] for day in stats["clicks_per_day"]) == 3
    assert len(stats["recent_clicks"]) == 3


# --- failure handling ---------------------------------------------------------


def test_database_outage_returns_503():
    with TestClient(create_app(TEST_SETTINGS, db=BrokenD1())) as client:
        assert client.get("/health").status_code == 200  # liveness does not depend on D1
        assert client.get("/abc1234").status_code == 503
        assert client.post("/auth/login", json={"username": "alice", "password": "whatever1"}).status_code == 503


def test_sql_error_returns_500(client, auth_headers, db):
    db.query("ALTER TABLE short_urls DROP COLUMN expires_at")  # App v2 against Schema v1
    response = client.post("/shorten", json={"original_url": "https://example.com"}, headers=auth_headers)
    assert response.status_code == 500
