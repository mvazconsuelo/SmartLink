"""Business analytics: clicks, clicks per day, top links.

This is product data stored in D1 and shown to users in the dashboard.
It is NOT technical observability (logs, errors, pod health), which goes
through stdout -> Alloy -> Loki -> Grafana.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from urllib.parse import urlsplit

from .database import Database, to_db_time, utcnow

USER_AGENT_MAX_LENGTH = 200
DAYS_WINDOW = 30
RECENT_LIMIT = 10


def _referrer_host(referrer: str | None) -> str | None:
    """Keep only the referring site, not the full URL (may contain personal data)."""
    if not referrer:
        return None
    host = urlsplit(referrer).hostname
    return host[:255] if host else None


def record_click(db: Database, short_url_id: int, referrer: str | None, user_agent: str | None) -> None:
    """Store one click and bump the link's counter, in one batch."""
    db.batch(
        [
            (
                "INSERT INTO click_events (short_url_id, clicked_at, referrer, user_agent) VALUES (?, ?, ?, ?)",
                [
                    short_url_id,
                    to_db_time(utcnow()),
                    _referrer_host(referrer),
                    user_agent[:USER_AGENT_MAX_LENGTH] if user_agent else None,
                ],
            ),
            ("UPDATE short_urls SET click_count = click_count + 1 WHERE id = ?", [short_url_id]),
        ]
    )


def _window_start() -> str:
    return to_db_time(utcnow() - timedelta(days=DAYS_WINDOW))


def url_stats(db: Database, short_url_id: int) -> dict[str, Any]:
    """Clicks per day (last 30 days) and the latest clicks of one link."""
    per_day = db.query(
        "SELECT substr(clicked_at, 1, 10) AS day, COUNT(*) AS clicks FROM click_events"
        " WHERE short_url_id = ? AND clicked_at >= ? GROUP BY day ORDER BY day",
        [short_url_id, _window_start()],
    ).rows
    recent = db.query(
        "SELECT clicked_at, referrer, user_agent FROM click_events"
        " WHERE short_url_id = ? ORDER BY clicked_at DESC, id DESC LIMIT ?",
        [short_url_id, RECENT_LIMIT],
    ).rows
    return {"clicks_per_day": per_day, "recent_clicks": recent}


def user_dashboard(db: Database, user_id: int) -> dict[str, Any]:
    """Totals, clicks per day, top links and latest clicks for one user."""
    now = to_db_time(utcnow())
    totals = db.query(
        "SELECT COUNT(*) AS total_urls,"
        " COALESCE(SUM(click_count), 0) AS total_clicks,"
        " COALESCE(SUM(CASE WHEN expires_at IS NOT NULL AND expires_at <= ? THEN 1 ELSE 0 END), 0) AS expired_urls"
        " FROM short_urls WHERE user_id = ?",
        [now, user_id],
    ).rows[0]
    per_day = db.query(
        "SELECT substr(c.clicked_at, 1, 10) AS day, COUNT(*) AS clicks"
        " FROM click_events c JOIN short_urls s ON s.id = c.short_url_id"
        " WHERE s.user_id = ? AND c.clicked_at >= ? GROUP BY day ORDER BY day",
        [user_id, _window_start()],
    ).rows
    top_links = db.query(
        "SELECT code, original_url, click_count FROM short_urls"
        " WHERE user_id = ? AND click_count > 0 ORDER BY click_count DESC, id LIMIT 5",
        [user_id],
    ).rows
    recent = db.query(
        "SELECT s.code, c.clicked_at, c.referrer FROM click_events c"
        " JOIN short_urls s ON s.id = c.short_url_id"
        " WHERE s.user_id = ? ORDER BY c.clicked_at DESC, c.id DESC LIMIT ?",
        [user_id, RECENT_LIMIT],
    ).rows
    return {
        "total_urls": totals["total_urls"],
        "total_clicks": totals["total_clicks"],
        "expired_urls": totals["expired_urls"],
        "clicks_per_day": per_day,
        "top_links": top_links,
        "recent_clicks": recent,
    }
