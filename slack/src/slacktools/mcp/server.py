from mcp.server.fastmcp import FastMCP

from slacktools import config
from slacktools.lists import api as lists_api
from slacktools.users import api as users_api

mcp = FastMCP("slacktools")


@mcp.tool()
def discover_lists() -> list[dict]:
    """Discover Slack Lists accessible in the workspace.

    Returns: list of {id, title} for each list.
    """
    return [
        {
            "id": entry.get("id"),
            "title": entry.get("title") or entry.get("name") or "(untitled)",
        }
        for entry in lists_api.discover_lists(config.load_token())
    ]


@mcp.tool()
def get_list_schema(list_id: str = "") -> list[dict]:
    """Return the column schema (id, key, type, name) for a Slack List.

    Args:
        list_id: List ID (e.g. F0B0MFZ6S9K). Empty -> use default from config.toml.
    """
    return lists_api.get_list_schema(config.load_token(), config.list_id_or_default(list_id))


@mcp.tool()
def list_items(list_id: str = "", limit: int = 100) -> dict:
    """Return items in a Slack List (raw API response).

    Args:
        list_id: List ID. Empty -> use default from config.toml.
        limit:   Max items to return (default 100).
    """
    return lists_api.list_items(
        config.load_token(), config.list_id_or_default(list_id), limit=limit
    )


@mcp.tool()
def add_list_item(
    fields: dict[str, str],
    list_id: str = "",
    parent_item_id: str = "",
) -> dict:
    """Add an item to a Slack List.

    Args:
        fields: Column key/id -> string value mapping. Examples:
                {"name": "Task title"}
                {"todo_assignee": "caleb"}      # user_id, email, or display name
                {"todo_due_date": "2026-05-07"} # ISO date
                {"todo_completed": "true"}      # bool-ish
                Text fields are wrapped as rich text automatically.
                User-type values that aren't already user_ids are auto-resolved.
        list_id: Target list ID. Empty -> use default from config.toml.
        parent_item_id: Optional parent item id (for subtasks).
    """
    return lists_api.create_item_from_kv(
        config.load_token(),
        config.list_id_or_default(list_id),
        fields,
        parent_item_id=parent_item_id or None,
    )


@mcp.tool()
def find_user(identifier: str) -> dict:
    """Resolve a Slack user record by id, email, or display/real name.

    Args:
        identifier: User_id (U...), email (foo@bar.com), or name ("caleb").
                    Name lookup uses a 7-day on-disk cache; first miss may take ~1s.
    """
    return users_api.find_user(config.load_token(), identifier)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
