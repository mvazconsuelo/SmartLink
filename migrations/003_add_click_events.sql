-- Schema v3: one row per click, for business analytics.
-- Deliberately no IP address: referrer is reduced to its host and the
-- user agent is truncated by the application before insert.

CREATE TABLE click_events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    short_url_id INTEGER NOT NULL REFERENCES short_urls (id),
    clicked_at   TEXT    NOT NULL,
    referrer     TEXT,
    user_agent   TEXT
);

CREATE INDEX idx_click_events_short_url_clicked_at
    ON click_events (short_url_id, clicked_at);
