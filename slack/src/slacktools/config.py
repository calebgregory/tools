import tomllib
import typing as ty
from functools import lru_cache
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.toml"


@lru_cache
def _load_config() -> dict[str, ty.Any]:
    if not _CONFIG_PATH.exists():
        return {}
    return tomllib.loads(_CONFIG_PATH.read_text())


def load_token() -> str:
    token_path_str = _load_config().get("api_keys", {}).get("slack_bot")
    if not token_path_str:
        raise OSError("slack_bot api_key filepath not found in config")
    token_path = Path(token_path_str).expanduser()
    if not token_path.exists():
        raise FileNotFoundError(f"Slack bot token not found at {token_path}")
    return str(token_path.read_text().strip())


def default_list_id() -> str | None:
    if configed := _load_config().get("lists", {}).get("default_id"):
        return str(configed)
    return None


def list_id_or_default(list_id: str = "") -> str:
    """Return the explicit list_id or fall back to [lists] default_id in config.toml.

    Raises:
        ValueError: if neither an explicit list_id nor a default is available.
    """
    resolved = list_id or default_list_id() or ""
    if not resolved:
        raise ValueError("No list_id provided and no default in config.toml")
    return resolved
