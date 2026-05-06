# Personal CLI tooling conventions

Defaults for personal Python CLI tools (typically under `~/tools/<name>/`):

- **CLI library:** `argh` (not click). Argparse-based, less ceremony for thin shells.
- **Install:** `uv tool install -e .` so edits are reflected immediately without reinstalling.
- **Config location:** inline with the tool — e.g. `~/tools/foo/config.toml` — not `~/.config/foo/`. Gitignore the config file.
- **Secrets:** secret material referenced from `config.toml` lives outside the tool's directory; ask where to point new secret references rather than assuming.
- **Project layout:** `pyproject.toml` + `src/<pkg>/` (hatchling build backend). Feature-first module organization (see [architectural-patterns.md](architectural-patterns.md)).

When scaffolding a new personal CLI, default to this stack. Confirm the install command and config location once when the tool is created; reuse the pattern thereafter.
