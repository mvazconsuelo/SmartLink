"""SmartLink API.

Run with the app factory (configuration is read from the environment):

    uvicorn app.main:create_app --factory --no-access-log
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse

from . import analytics, shortener
from .auth import CurrentUser, UsernameTaken, authenticate, create_access_token, create_user, get_current_user
from .config import Settings
from .database import D1Database, Database, DatabaseUnavailable, QueryError, from_db_time
from .qr import qr_png
from .schemas import Credentials, Dashboard, ShortenRequest, ShortUrl, ShortUrlDetail, Token

logger = logging.getLogger("smartlink.api")

# Kubernetes probes call /health every few seconds; logging them at INFO
# would bury the useful lines in Loki.
QUIET_PATHS = {"/health"}


def configure_logging(level: str) -> None:
    """One key=value line per event, to stdout, for Alloy to collect."""
    # One line per event, key=value pairs: readable by humans and parseable
    # in Loki with `| logfmt`. Everything goes to stdout for Alloy to collect.
    logging.basicConfig(
        level=level,
        format="%(asctime)s level=%(levelname)s logger=%(name)s msg=%(message)s",
        force=True,
    )
    # httpx logs every D1 call at INFO; database.py already logs failures.
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_db(request: Request) -> Database:
    """FastAPI dependency: the database the app was created with."""
    return request.app.state.db


def _to_short_url(row: dict[str, Any], base_url: str) -> dict[str, Any]:
    return {
        "code": row["code"],
        "short_url": f"{base_url}/{row['code']}",
        "original_url": row["original_url"],
        "created_at": from_db_time(row["created_at"]),
        "expires_at": from_db_time(row["expires_at"]),
        "status": shortener.link_status(row),
        "click_count": row["click_count"],
    }


def create_app(settings: Settings | None = None, db: Database | None = None) -> FastAPI:
    """Build the API. Settings come from the environment unless given; db is replaced in tests."""
    settings = settings or Settings.from_env()
    configure_logging(settings.log_level)

    if db is None:
        db = D1Database(
            account_id=settings.d1_account_id,
            database_id=settings.d1_database_id,
            api_token=settings.d1_api_token,
            timeout_seconds=settings.d1_timeout_seconds,
        )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Log the startup and close the database on shutdown."""
        logger.info("smartlink api starting public_base_url=%s", settings.public_base_url)
        yield
        app.state.db.close()

    app = FastAPI(title="SmartLink API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.db = db
    base_url = settings.public_base_url

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log every request (method, path, status, duration) and turn crashes into a 500."""
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("unhandled error method=%s path=%s", request.method, request.url.path)
            response = JSONResponse({"detail": "Internal server error"}, status_code=500)
        duration_ms = round((time.perf_counter() - started) * 1000)
        level = logging.DEBUG if request.url.path in QUIET_PATHS and response.status_code < 400 else logging.INFO
        if response.status_code >= 500:
            level = logging.ERROR
        logger.log(
            level,
            "request method=%s path=%s status=%s duration_ms=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    @app.exception_handler(DatabaseUnavailable)
    async def database_unavailable(request: Request, exc: DatabaseUnavailable):
        """D1 cannot be reached: 503."""
        return JSONResponse({"detail": "Database unavailable"}, status_code=503)

    @app.exception_handler(QueryError)
    async def query_error(request: Request, exc: QueryError):
        """D1 rejected the SQL: 500."""
        return JSONResponse({"detail": "Internal server error"}, status_code=500)

    @app.get("/health")
    def health() -> dict[str, str]:
        """Liveness probe: the process is up. Does not check D1."""
        # Liveness only: the process is up and serving HTTP. It deliberately
        # does NOT check D1, so a D1 outage does not make Kubernetes restart
        # healthy pods (restarting would not fix an external dependency).
        return {"status": "ok"}

    @app.post("/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
    def register(body: Credentials, db: Database = Depends(get_db)):
        """Create an account and return a token."""
        if not settings.allow_registration:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Registration is disabled")
        try:
            user = create_user(db, body.username, body.password)
        except UsernameTaken:
            raise HTTPException(status.HTTP_409_CONFLICT, "Username already exists") from None
        logger.info("user registered user_id=%s", user.id)
        return Token(access_token=create_access_token(user, settings.jwt_secret, settings.jwt_ttl_minutes))

    @app.post("/auth/login", response_model=Token)
    def login(body: Credentials, db: Database = Depends(get_db)):
        """Check the credentials and return a token."""
        user = authenticate(db, body.username, body.password)
        if user is None:
            logger.info("login failed")
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
        logger.info("login ok user_id=%s", user.id)
        return Token(access_token=create_access_token(user, settings.jwt_secret, settings.jwt_ttl_minutes))

    @app.post("/shorten", response_model=ShortUrl, status_code=status.HTTP_201_CREATED)
    def shorten(
        body: ShortenRequest,
        user: CurrentUser = Depends(get_current_user),
        db: Database = Depends(get_db),
    ):
        """Create a short link, with an optional alias and expiration."""
        try:
            row = shortener.create_short_url(db, user.id, str(body.original_url), body.custom_alias, body.expires_at)
        except shortener.InvalidAlias:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "Alias must be 3-32 characters (letters, digits, '-', '_') and not a reserved word",
            ) from None
        except shortener.AliasTaken:
            raise HTTPException(status.HTTP_409_CONFLICT, "Alias already in use") from None
        except shortener.InvalidExpiration:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "expires_at must be in the future") from None
        return _to_short_url(row, base_url)

    @app.get("/urls", response_model=list[ShortUrl])
    def list_urls(user: CurrentUser = Depends(get_current_user), db: Database = Depends(get_db)):
        """The signed-in user's links."""
        return [_to_short_url(row, base_url) for row in shortener.list_user_urls(db, user.id)]

    def _owned(db: Database, user: CurrentUser, code: str) -> dict[str, Any]:
        try:
            return shortener.get_user_url(db, user.id, code)
        except shortener.LinkNotFound:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Short URL not found") from None

    @app.get("/urls/{code}", response_model=ShortUrlDetail)
    def url_detail(code: str, user: CurrentUser = Depends(get_current_user), db: Database = Depends(get_db)):
        """One of your links, with its click statistics."""
        row = _owned(db, user, code)
        return {**_to_short_url(row, base_url), **analytics.url_stats(db, row["id"])}

    @app.get("/urls/{code}/qr", responses={200: {"content": {"image/png": {}}}})
    def url_qr(code: str, user: CurrentUser = Depends(get_current_user), db: Database = Depends(get_db)):
        """The QR code of one of your links, as a PNG."""
        row = _owned(db, user, code)
        return Response(qr_png(f"{base_url}/{row['code']}"), media_type="image/png")

    @app.get("/stats", response_model=Dashboard)
    def stats(user: CurrentUser = Depends(get_current_user), db: Database = Depends(get_db)):
        """Your totals, clicks per day, top links and latest clicks."""
        return analytics.user_dashboard(db, user.id)

    # Must be registered last: it matches any single path segment.
    @app.get("/{code}")
    def redirect(code: str, request: Request, db: Database = Depends(get_db)):
        """Send the visitor to the target (302) and record the click. 404 unknown, 410 expired."""
        try:
            row = shortener.resolve(db, code)
        except shortener.LinkNotFound:
            logger.info("redirect not_found code=%s", code)
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Short URL not found") from None
        except shortener.LinkExpired:
            logger.info("redirect expired code=%s", code)
            raise HTTPException(status.HTTP_410_GONE, "Short URL has expired") from None

        # A failure to record analytics must not break the redirect: the user
        # still gets where they were going; the lost click is logged.
        try:
            analytics.record_click(db, row["id"], request.headers.get("referer"), request.headers.get("user-agent"))
            logger.info("click recorded code=%s", code)
        except (DatabaseUnavailable, QueryError):
            logger.error("click not recorded code=%s", code)

        logger.info("redirect code=%s", code)
        # 302, not 301: browsers cache 301 forever and later clicks would
        # never reach SmartLink (no analytics, no expiration).
        return RedirectResponse(row["original_url"], status_code=status.HTTP_302_FOUND)

    return app
