"""OAuth against the Gmail API, using Google's installed-app (desktop) flow.

The first call opens a browser for consent and caches the resulting refresh token, so
every later call is non-interactive until the token is revoked.
"""

import logging
import typing as ty

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from tools.env import SECRET_DIR, require_env

logger = logging.getLogger(__name__)

_TOKEN_FILE = SECRET_DIR / "gmail-token.json"

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
"""`gmail.modify` can label and trash but cannot delete for good; that needs the full
`https://mail.google.com/` scope, which these tools deliberately do not ask for. A
trashed message is recoverable for 30 days, and that window is the safety net for a
sender match that turns out to be broader than intended."""


def _client_config() -> dict[str, ty.Any]:
    gmail = require_env().gmail
    if not (gmail.client_id and gmail.client_secret):
        raise EnvironmentError(
            "no Gmail OAuth client in .env.toml — add [gmail] client_id and client_secret"
        )
    return {
        "installed": {
            "client_id": gmail.client_id,
            "client_secret": gmail.client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def _cached() -> Credentials | None:
    if not _TOKEN_FILE.exists():
        return None
    cached: Credentials = Credentials.from_authorized_user_file(str(_TOKEN_FILE), SCOPES)
    return cached


def _persist(credentials: Credentials) -> None:
    SECRET_DIR.mkdir(parents=True, exist_ok=True)
    _TOKEN_FILE.write_text(credentials.to_json())
    _TOKEN_FILE.chmod(0o600)


def credentials() -> Credentials:
    cached = _cached()
    if cached and cached.valid:
        return cached

    if cached and cached.expired and cached.refresh_token:
        logger.info("refreshing the cached Gmail token")
        cached.refresh(Request())
        _persist(cached)
        return cached

    logger.info("no usable cached token; opening a browser for consent")
    fresh: Credentials = InstalledAppFlow.from_client_config(_client_config(), SCOPES).run_local_server(
        port=0
    )
    _persist(fresh)
    return fresh
