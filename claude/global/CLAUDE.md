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
