# slacktools

Personal Slack tooling: a CLI and an MCP server backed by a single Python API core. Currently focused on Slack Lists (with planned expansion to canvases and beyond).

## Purpose

Slack's first-party connector exposes messages, channels, threads, search, and canvases — but not Lists. This project fills that gap so that Slack Lists become first-class objects in personal workflows: discoverable from the terminal, scriptable, and callable as MCP tools from Claude Code.

Two surfaces, one core:

- **CLI** — `slack lists ...`, `slack users ...` for ad-hoc terminal use.
- **MCP server** — `slack-mcp` exposes the same operations as tools to Claude Code.

Both surfaces import from `slacktools/lists/api.py` and `slacktools/users/api.py`, so improvements land in both at once.

## Requirements

- Slack workspace on a paid plan (Lists API requirement).
- Python 3.11+.
- [uv](https://docs.astral.sh/uv/).
- A Slack app installed in your workspace with the scopes listed in [`manifest.yaml`](./manifest.yaml). Justification text for an install request is in [`permissions.md`](./permissions.md).

## Setup

1. **Create the Slack app.** At `api.slack.com/apps`, create a new app from the manifest in this repo (`From an app manifest` → paste `manifest.yaml`).
2. **Install and copy the user OAuth token.** This is the `xoxp-…` token from the *OAuth & Permissions* page after install.
3. **Stash the token.** Plain file under `~/.keys/`, e.g. `~/.keys/slack-bot-caleb-gregory-slack-app.txt`.
4. **Configure.** Edit `config.toml` in this directory:

   ```toml
   [lists]
   default_id = "F0123456789"  # the list_id you want as default; optional

   [api_keys]
   slack_bot = '~/.keys/slack-bot-caleb-gregory-slack-app.txt'
   ```

5. **Install the tool.**

   ```bash
   uv tool install -e .
   ```

   Installs two executables: `slack` (CLI) and `slack-mcp` (MCP server). The `-e` (editable) flag means source edits are picked up on the next invocation without reinstalling.

## CLI usage

### Lists

```bash
slack lists discover                                       # all list_ids you can see
slack lists columns [LIST_ID]                              # column ids/keys/types
slack lists ls [LIST_ID]                                   # raw item dump
slack lists add \
  --field name='Task title' \
  --field todo_assignee=caleb \
  --field todo_due_date=2026-05-07
```

`LIST_ID` is optional anywhere it appears — falls back to `[lists] default_id` in `config.toml`.

`--field` accepts either a column key (`name`, `todo_assignee`) or a column id (`Col0…`). Repeatable. Type-specific encoding (rich text wrapping for text fields, array wrapping for users/dates, etc.) is handled automatically. User-type values that aren't already user_ids are auto-resolved (see Users below).

### Users

```bash
slack users find <id|email|name>     # one-line summary
slack users info <id|email|name>     # full user record (JSON)
slack users sync                     # force-refresh the directory cache
```

Resolution paths:
- `U…` / `W…` → `users.info`
- contains `@` → `users.lookupByEmail`
- otherwise → case-insensitive substring match against display_name / real_name in a local cache, populated lazily from `users.list`

The cache lives at `~/.cache/slacktools/users.json` with a 7-day TTL. Cold lookup ~1s; warm ~80ms. Multiple matches raise rather than guess.

## MCP server

Register with Claude Code (user scope, available across all projects):

```bash
claude mcp add slacktools --scope user $(which slack-mcp)
```

Restart Claude Code (or `/mcp` → reconnect). Available tools:

- `mcp__slacktools__discover_lists`
- `mcp__slacktools__get_list_schema`
- `mcp__slacktools__list_items`
- `mcp__slacktools__add_list_item` — accepts a `fields` dict, with auto-resolution of user-type values
- `mcp__slacktools__find_user`

The server is stdio JSON-RPC — verify directly with:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}' | slack-mcp
```

## Architecture

Feature-first module layout. Each feature ships an `api.py` (pure-ish core) and a `cli.py` (argh-decorated subcommands). Surfaces (CLI dispatcher, MCP server) live in their own modules and import the per-feature cores.

```
src/slacktools/
  _http.py            # shared HTTP helpers (get, post, SlackAPIError)
  config.py           # token + default list_id loading
  lists/
    api.py            # Slack Lists / files endpoints, kv helpers, type formatting
    cli.py            # `slack lists ...`
  users/
    api.py            # users.* endpoints + on-disk directory cache
    cli.py            # `slack users ...`
  cli/__main__.py     # argh dispatcher → registers feature commands as subgroups
  mcp/server.py       # FastMCP server → registers feature functions as tools
```

Adding a new feature: drop `<feature>/{api,cli}.py`, register the CLI commands in `cli/__main__.py`, expose the API functions as tools in `mcp/server.py`. The two shells stay thin; logic stays in the feature `api.py`.

## Caveats

- **List schemas are fetched via `files.info`** — Slack stores Lists as files internally, so `files:read` is required.
- **Email lookup needs `users:read.email`** — without it the email path 401s; the id and name paths still work.
- **Name resolution is case-insensitive substring** with a "raise on multiple matches" rule. Common first names in large workspaces will need a fuller identifier.
- **User-token identity** — everything the script does shows up as you in Slack audit logs. Don't bind this to anything that should look bot-driven.
