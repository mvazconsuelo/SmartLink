"""Configuration from environment variables (12-factor).

In Kubernetes these come from a ConfigMap (non-secret values) and a Secret
(D1_API_TOKEN, JWT_SECRET). Nothing here has a default for a secret value:
the app must fail at startup instead of running with an insecure fallback.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """A required variable is missing or invalid: the app refuses to start."""


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(f"missing required environment variable {name}")
    return value


@dataclass(frozen=True)
class Settings:
    """Application settings, read once at startup and never modified."""

    jwt_secret: str
    public_base_url: str
    d1_account_id: str = ""
    d1_database_id: str = ""
    d1_api_token: str = ""
    d1_timeout_seconds: float = 5.0
    jwt_ttl_minutes: int = 60
    allow_registration: bool = True
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> Settings:
        """Read and validate the environment. Raises ConfigError instead of using an insecure default."""
        jwt_secret = _required("JWT_SECRET")
        if len(jwt_secret) < 32:
            # RFC 7518: HS256 keys must be at least 256 bits.
            raise ConfigError("JWT_SECRET must be at least 32 characters (try: openssl rand -hex 32)")
        return cls(
            jwt_secret=jwt_secret,
            public_base_url=_required("PUBLIC_BASE_URL").rstrip("/"),
            d1_account_id=_required("D1_ACCOUNT_ID"),
            d1_database_id=_required("D1_DATABASE_ID"),
            d1_api_token=_required("D1_API_TOKEN"),
            d1_timeout_seconds=float(os.environ.get("D1_TIMEOUT_SECONDS", "5")),
            jwt_ttl_minutes=int(os.environ.get("JWT_TTL_MINUTES", "60")),
            allow_registration=os.environ.get("ALLOW_REGISTRATION", "true").lower() == "true",
            log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        )
