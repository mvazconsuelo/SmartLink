"""Request/response models of the public API."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator


class Credentials(BaseModel):
    """Username and password, for both register and login."""

    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)


class Token(BaseModel):
    """The JWT returned by register and login."""

    access_token: str
    token_type: str = "bearer"


class ShortenRequest(BaseModel):
    """A URL to shorten, with an optional alias and expiration."""

    # AnyHttpUrl only accepts http/https, so javascript: or data: URLs are rejected.
    original_url: AnyHttpUrl
    custom_alias: str | None = None
    expires_at: date | datetime | None = Field(
        default=None,
        description="A date (link valid until the end of that day, UTC) or a datetime.",
    )

    @field_validator("expires_at")
    @classmethod
    def normalize_expiration(cls, value: date | datetime | None) -> datetime | None:
        """A date means the end of that day (UTC); a datetime is converted to UTC."""
        if value is None:
            return None
        if not isinstance(value, datetime):
            return datetime.combine(value + timedelta(days=1), time.min, tzinfo=UTC)
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class ShortUrl(BaseModel):
    """A short link as the API returns it."""

    code: str
    short_url: str
    original_url: str
    created_at: datetime
    expires_at: datetime | None
    status: str
    click_count: int


class DailyClicks(BaseModel):
    """Clicks on one day (YYYY-MM-DD, UTC)."""

    day: str
    clicks: int


class Click(BaseModel):
    """One recorded click. Only the referring site is kept, not the full URL."""

    clicked_at: datetime
    referrer: str | None = None
    user_agent: str | None = None
    code: str | None = None


class ShortUrlDetail(ShortUrl):
    """A short link plus its click statistics."""

    clicks_per_day: list[DailyClicks]
    recent_clicks: list[Click]


class TopLink(BaseModel):
    """A link ranked by its clicks."""

    code: str
    original_url: str
    click_count: int


class Dashboard(BaseModel):
    """A user's totals, clicks per day, top links and latest clicks."""

    total_urls: int
    total_clicks: int
    expired_urls: int
    clicks_per_day: list[DailyClicks]
    top_links: list[TopLink]
    recent_clicks: list[Click]
