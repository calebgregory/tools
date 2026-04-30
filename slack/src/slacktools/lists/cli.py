import json
import typing as ty

import argh

from slacktools import config
from slacktools.lists import api


def discover() -> None:
    """Find lists in the workspace."""
    lists = api.discover_lists(config.load_token())

    if not lists:
        print("No lists found.")
        return

    for entry in lists:
        title = entry.get("title") or entry.get("name") or "(untitled)"
        print(f"{entry.get('id')}\t{title}")


def columns(list_id: str = "") -> None:
    """Show columns of a list (uses default if omitted)."""
    schema = api.get_list_schema(config.load_token(), config.list_id_or_default(list_id))

    if not schema:
        print("No columns found.")
        return

    for col in schema:
        primary = " (primary)" if col.get("is_primary_column") else ""
        print(f"{col.get('id')}\t{col.get('key')}\t{col.get('type')}\t{col.get('name')}{primary}")


def ls(list_id: str = "", limit: int = 100) -> None:
    """List items in a list (uses default if omitted)."""
    data = api.list_items(config.load_token(), config.list_id_or_default(list_id), limit=limit)

    print(json.dumps(data, indent=2))


@argh.arg("--field", "-f", action="append", help="column_key_or_id=value (repeatable)")
def add(field: ty.Collection[str] = (), list_id: str = "", parent: str = "") -> None:
    """Add an item to a list. Use --field column_key_or_id=value (repeatable)."""
    if not field:
        raise ValueError("At least one --field column_key_or_id=value is required.")

    fields_dict: dict[str, str] = {}
    for f in field:
        if "=" not in f:
            raise ValueError(f"Invalid --field {f!r}; expected column_key_or_id=value")
        key, _, value = f.partition("=")
        fields_dict[key] = value

    result = api.create_item_from_kv(
        config.load_token(),
        config.list_id_or_default(list_id),
        fields_dict,
        parent_item_id=parent or None,
    )

    print(json.dumps(result, indent=2))
