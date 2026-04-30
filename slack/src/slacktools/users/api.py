import functools
import json
import pathlib
import re
import time
import typing as ty

from slacktools import _http

_USER_ID_RE = re.compile(r"^[UW][A-Z0-9]{8,}$")
CACHE_PATH = pathlib.Path.home() / ".cache" / "slacktools" / "users.json"
_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60

_P = ty.ParamSpec("_P")
_R = ty.TypeVar("_R")


class _FileCached(ty.Generic[_P, _R]):
    def __init__(self, fn: ty.Callable[_P, _R], file: pathlib.Path, ttl_seconds: float) -> None:
        self._fn = fn
        self._file = file
        self._ttl_seconds = ttl_seconds
        functools.update_wrapper(self, fn)

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        if self._file.exists():
            cache = json.loads(self._file.read_text())
            if (time.time() - cache.get("fetched_at", 0)) <= self._ttl_seconds:
                return ty.cast(_R, cache["result"])
        return self.refresh(*args, **kwargs)

    def refresh(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        result = self._fn(*args, **kwargs)
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(json.dumps({"fetched_at": int(time.time()), "result": result}))
        return result


def _cached_in_file(
    file: pathlib.Path, ttl_seconds: float
) -> ty.Callable[[ty.Callable[_P, _R]], _FileCached[_P, _R]]:
    def decorator(fn: ty.Callable[_P, _R]) -> _FileCached[_P, _R]:
        return _FileCached(fn, file, ttl_seconds)

    return decorator


def looks_like_user_id(s: str) -> bool:
    return bool(_USER_ID_RE.match(s))


def get_user_info(token: str, user_id: str) -> dict:
    return dict(_http.get(token, "users.info", {"user": user_id})["user"])


def lookup_by_email(token: str, email: str) -> dict:
    return dict(_http.get(token, "users.lookupByEmail", {"email": email})["user"])


@_cached_in_file(CACHE_PATH, _CACHE_TTL_SECONDS)
def list_all(token: str) -> list[dict]:
    """Paginate users.list and return all members."""
    members: list[dict] = []
    cursor = ""
    while True:
        params: dict[str, ty.Any] = {"limit": 200}
        if cursor:
            params["cursor"] = cursor
        resp = _http.get(token, "users.list", params)
        members.extend(resp.get("members", []))
        cursor = resp.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            break
    return members


def _find_matching_user(users: list[dict], name: str) -> dict | None:
    """Case-insensitive substring match on display_name/real_name/name. Raises if ambiguous."""
    target = name.lower().lstrip("@")

    matches: list[dict] = []
    for user in users:
        if user.get("deleted") or user.get("is_bot"):
            continue
        profile = user.get("profile", {})
        candidates = [
            profile.get("display_name") or "",
            profile.get("real_name") or "",
            user.get("name") or "",
        ]
        if any(c and target in c.lower() for c in candidates):
            matches.append(user)

    if not matches:
        return None

    if len(matches) > 1:
        summary = ", ".join(
            f"{u.get('profile', {}).get('real_name')}({u['id']})" for u in matches[:5]
        )
        raise ValueError(f"Ambiguous match for {name!r}: {len(matches)} users — {summary}")

    return matches[0]


def find_user(token: str, identifier: str) -> dict:
    """Resolve user_id, email, or name (display/real) to a user record."""
    if looks_like_user_id(identifier):
        return get_user_info(token, identifier)

    if "@" in identifier:
        return lookup_by_email(token, identifier)

    if match := _find_matching_user(list_all(token), identifier):
        return match

    if match := _find_matching_user(list_all.refresh(token), identifier):
        return match

    raise ValueError(f"No user matching {identifier!r}")
