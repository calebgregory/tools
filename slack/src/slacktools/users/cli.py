import json

from slacktools import config
from slacktools.users import api


def find(identifier: str) -> None:
    """Resolve a user_id, email, or display/real name to a user record."""
    user = api.find_user(config.load_token(), identifier)

    profile = user.get("profile", {})
    name = profile.get("display_name") or profile.get("real_name")
    print(f"{user.get('id')}\t{name}\t{profile.get('email', '')}")


def sync() -> None:
    """Refresh the local user-directory cache."""
    users = api.list_all.refresh(config.load_token())

    print(f"Cached {len(users)} users to {api.CACHE_PATH}")


def info(identifier: str) -> None:
    """Print full user record JSON for a resolved identifier."""
    user = api.find_user(config.load_token(), identifier)

    print(json.dumps(user, indent=2))
