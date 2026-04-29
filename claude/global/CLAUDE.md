# CLAUDE.md

## principle extraction

When the user corrects your code or gives a stylistic/architectural instruction that sounds like a general principle (not a one-off), suggest running `/extract-principle`.

## Editing `ml-collab` files via Obsidian CLI

- **CRITICAL**: Before editing any file under `ml-collab` on disk, first run
  `obsidian-cli vault=<name> open path="<vault-relative-path>" newtab`
  so that Relay (the live-sync plugin) is aware of the file. Then edit the file directly
  on disk with normal tools.
- `vault=<name>` must come **before** the `open` command. Run `obsidian-cli vaults` to
  list registered vault names.
- `path=` is relative to the vault root, never absolute. Example:
  `path="ml-collab/foo.md"`.
- Obsidian must be running; if it isn't, the first CLI command launches it.

## Slack MCP connector availability

The Slack MCP connector (installed via claude.ai/console) intermittently fails to surface its
tools at session start. If a session appears to lack Slack tools, do **not** assume the connector
is unavailable — check the deferred-tools list for `mcp__claude_ai_Slack__*` entries and load them
via `ToolSearch` before concluding otherwise.

If the tools genuinely aren't present and the user expects them, mention the workaround: uninstall
and reinstall the connector in the Claude console, then retry. The user has confirmed this is a
recurring connector bug, not user error.

Tool name prefix to search for: `mcp__claude_ai_Slack__` (e.g. `slack_read_channel`,
`slack_send_message`, `slack_search_channels`).
