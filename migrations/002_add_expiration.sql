-- Schema v2: optional expiration date per short URL.
-- Additive change: existing rows get NULL (= never expires), so App v1 keeps
-- working against Schema v2. The reverse (App v2 on Schema v1) does not.

ALTER TABLE short_urls ADD COLUMN expires_at TEXT;
