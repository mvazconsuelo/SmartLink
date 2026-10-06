-- Schema v1: users and their short URLs.
-- Timestamps are stored as UTC text 'YYYY-MM-DD HH:MM:SS' so they sort and
-- compare correctly as strings and work with SQLite date functions.

CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL
);

CREATE TABLE short_urls (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users (id),
    code         TEXT    NOT NULL UNIQUE,
    original_url TEXT    NOT NULL,
    created_at   TEXT    NOT NULL,
    is_active    INTEGER NOT NULL DEFAULT 1,
    click_count  INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_short_urls_user_id ON short_urls (user_id);
