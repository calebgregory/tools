import typing as ty

from slacktools import _http
from slacktools.users import api as users_api

# Re-export for backward compatibility within the package.
SlackAPIError = _http.SlackAPIError


def discover_lists(token: str) -> list[dict]:
    """Find lists in the workspace via files.list (Slack stores Lists as files)."""
    data = _http.get(token, "files.list", {"types": "lists"})
    return list(data.get("files", []))


def get_list_info(token: str, list_id: str) -> dict:
    """Return the file/list metadata, including schema, via files.info."""
    return _http.get(token, "files.info", {"file": list_id})


def get_list_schema(token: str, list_id: str) -> list[dict]:
    """Return the column schema for a list."""
    info = get_list_info(token, list_id)
    return list(info.get("file", {}).get("list_metadata", {}).get("schema", []))


def list_items(token: str, list_id: str, limit: int = 100) -> dict:
    """Return items + schema for a list. Raw API response."""
    return _http.post(token, "slackLists.items.list", {"list_id": list_id, "limit": limit})


def create_item(
    token: str,
    list_id: str,
    initial_fields: list[dict],
    parent_item_id: str | None = None,
) -> dict:
    payload: dict[str, ty.Any] = {"list_id": list_id, "initial_fields": initial_fields}
    if parent_item_id:
        payload["parent_item_id"] = parent_item_id
    return _http.post(token, "slackLists.items.create", payload)


def _resolve_column(schema: list[dict], identifier: str) -> dict:
    """Resolve a column by id, key, or (case-insensitive) name."""
    for col in schema:
        if col.get("id") == identifier or col.get("key") == identifier:
            return col
    target = identifier.lower()
    for col in schema:
        if (col.get("name") or "").lower() == target:
            return col
    available = ", ".join(f"{c.get('name')!r}({c.get('id')})" for c in schema)
    raise ValueError(f"Unknown column {identifier!r}. Available: {available}")


# Column types whose API representation is `{column_id, <api_property>: [raw_value]}`.
# Maps the Slack column type → the API property name that holds the value.
_ARRAY_TYPES = {
    "todo_assignee": "user",
    "user": "user",
    "todo_due_date": "date",
    "date": "date",
    "email": "email",
    "phone": "phone",
    "channel": "channel",
}
_NUMERIC_ARRAY_TYPES = {"number", "rating"}
_BOOL_TRUE_VALUES = {"true", "1", "yes", "y", "on"}


def _text_block(raw_value: str) -> dict:
    return {
        "type": "rich_text",
        "elements": [
            {
                "type": "rich_text_section",
                "elements": [{"type": "text", "text": raw_value}],
            }
        ],
    }


def _format_select(col: dict, raw_value: str) -> dict:
    """Translate label-or-option-id values into option-ids; supports comma-separated for multi_select."""
    options = col.get("options", {}) or {}
    fmt = options.get("format", "single_select")
    choices = options.get("choices", []) or []
    label_to_value = {(c.get("label") or "").lower(): c["value"] for c in choices if c.get("label")}
    valid_values = {c["value"] for c in choices}
    raw_values = [v.strip() for v in raw_value.split(",")] if fmt == "multi_select" else [raw_value]
    resolved: list[str] = []
    for v in raw_values:
        if v in valid_values:
            resolved.append(v)
        elif v.lower() in label_to_value:
            resolved.append(label_to_value[v.lower()])
        else:
            available = sorted(c.get("label") or "" for c in choices)
            raise ValueError(
                f"Unknown select value {v!r} for column {col['id']} ({col.get('name')!r}). "
                f"Valid labels: {available}"
            )
    return {"column_id": col["id"], "select": resolved}


def _format_field(col: dict, raw_value: str) -> dict:
    """Format a raw string value into the type-specific field structure the API expects."""
    col_id = col["id"]
    col_type = col["type"]

    if col_type == "text":
        return {"column_id": col_id, "rich_text": [_text_block(raw_value)]}
    if col_type in ("todo_completed", "checkbox"):
        return {"column_id": col_id, "checkbox": raw_value.strip().lower() in _BOOL_TRUE_VALUES}
    if col_type == "select":
        return _format_select(col, raw_value)
    if (api_property := _ARRAY_TYPES.get(col_type)) is not None:
        return {"column_id": col_id, api_property: [raw_value]}
    if col_type in _NUMERIC_ARRAY_TYPES:
        return {"column_id": col_id, col_type: [int(raw_value)]}
    raise ValueError(f"Unsupported column type {col_type!r} for column {col_id}")


def create_item_from_kv(
    token: str,
    list_id: str,
    fields: dict[str, str],
    parent_item_id: str | None = None,
) -> dict:
    """Create an item from a {column_key_or_id: raw_value} mapping.

    Resolves each identifier against the list schema and formats values per column type.
    User-type fields whose value is not already a Slack user_id are pre-resolved via
    the users module (email lookup or cached name match).
    """
    schema = get_list_schema(token, list_id)
    initial_fields = []
    for key, val in fields.items():
        col = _resolve_column(schema, key)
        if col["type"] in ("todo_assignee", "user") and not users_api.looks_like_user_id(val):
            val = users_api.find_user(token, val)["id"]
        initial_fields.append(_format_field(col, val))
    return create_item(token, list_id, initial_fields, parent_item_id)
