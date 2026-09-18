# Development environment

## Run the project's tool, not the global one

A linter, formatter, type checker or test runner should be the version the project pins. Resolve it by
walking up from the file to the repo root and taking the first project environment that carries the tool
(e.g. `.venv/bin/ruff`); fall back to a global install only when none does. The walk goes upward because
a monorepo sometimes installs the tool once at the repo root, while each project underneath has an
environment without it.

Versions differ in which rules they enforce, not just in bug fixes — a newer global copy flags and
auto-fixes what the project never opted into, and the editor stops agreeing with CI.

## Keep personal tool preferences out of shared project config

When a tool's behavior bothers you in your editor, change it in your editor's configuration, not in the
repo's committed config. Silencing a lint rule in `pyproject.toml` to stop something happening on-save in
a text editor changes the project for everyone and for CI in order to fix one person's workflow.

The question to ask is whose problem it is. A rule the project genuinely should not enforce belongs in
the project config; a rule you personally do not want applied to your keystrokes belongs in your editor.
