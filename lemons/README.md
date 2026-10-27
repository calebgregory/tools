# Agent context

[Shared instructions and workflows](_shared/) serve Claude and Codex. General
coding and writing guidance lives in [principles](../principles/). Harness-specific
configuration and startup adapters live in [claude](claude/) and [codex](codex/).

Obsidian Sync ignores hidden directories. Vault-level `.claude` configuration lives
in this repository and is linked into each vault so it remains version controlled
and can be installed on another machine.

Projects with their own Git repositories keep `.claude/` in the project. For
example, the wedding project under `~/_/main/projects/` owns skills and agents that
use project-relative paths and will be archived with the project.

## Install

```sh
cd ~/tools/lemons
./claude/bootstrap.py
./codex/bootstrap.py
```

The scripts run through `uv run`, which resolves this package from the current
directory, so run them from this directory. `uv` installs the package's
dependencies (the repository's `tools` package and its `thds` libraries) into
`.venv` on first run. If `.env.toml` is missing, the bootstrap copies
[.env.template.toml](../.env.template.toml) and asks you to fill it out.

Configure `[lemons.project-targets]` in `~/tools/.env.toml`. Each key names a
subdirectory of [_shared](_shared/); each value names the project to configure.
`[lemons.auto-memory-paths]` overrides the path used for Claude's auto-memory key.
Existing `[claude]` mappings remain readable until the machine's config is migrated.

Claude receives its global settings and instruction adapter, a link to principles
as `~/.claude/rules`, and individual skill links directly into `~/.claude/skills`
and `<project>/.claude/skills`. The bootstrap links every file in a project adapter
under [claude](claude/) (except `README.md` and `.gitignore`), plus the shared output
styles, individually into the real project `.claude` directory. Project memory and
Claude's automatic memory directory link to the shared project memory.

Codex receives its [startup adapter](codex/AGENTS.md), global skill links under
`~/.agents/skills`, project skill links under `<project>/.agents/skills`, and a
link to the project's adapter under [codex](codex/) as `<project>/AGENTS.md`.
Codex reads `AGENTS.md` only from the project root, not from a hidden directory,
so the link is visible there (including in an Obsidian vault). The global adapter
reads the shared instructions and principles at startup; the project adapter names
the shared project files to read. Restart sessions after installing to verify the
new context.

`CLAUDE_CONFIG_DIR` and `CODEX_HOME` override the corresponding harness config
locations. Codex's user skill links still use `~/.agents/skills`.

## Existing installations

Both harnesses own their configuration and skill directories. Bootstrap installs
individual authored skills there; internal directories such as `.trash` and
`synced` belong to the harness and stay outside this repository. New shared skills
appear when the corresponding bootstrap runs again. The bootstrap removes links in
those directories that point into this tree but no longer have a source, and leaves
other links alone.

The bootstraps replace existing symlinks and report conflicting regular files or
directories before installing anything. Existing real configuration directories
are merged with the managed entries. Legacy directory links for project `.claude`
and skill directories are converted into real local directories. The migration
moves unmanaged entries into those local directories, preserving their contents. That
includes `.trash` and `synced`, which earlier installs stored in the shared tree. The
bootstrap refuses to move a real file or directory from this repository that no link
manages; move or delete it, then rerun.

Project `.claude` directories tracked by their own repositories remain owned by
those projects; do not add them to the mappings unless you intend to replace them
with managed entries. The bootstrap refuses to overwrite an existing regular file
or directory at an individual link destination. The usual collision is
`~/.claude/projects/<key>/memory`, which Claude Code creates on its own; merge its
contents into the shared project memory and remove it, then rerun.
Mapped project roots must already exist; the bootstrap will not create a vault or
project directory for a missing or mistyped target.

### Migrating a machine from the `~/tools/claude` layout

After pulling this layout, the old `~/tools/claude` tree is gone except for
gitignored leftovers, and the links an earlier bootstrap wrote point into it.

1. Move `~/tools/claude/work-org/settings.local.json` to
   [claude/work-org/](claude/work-org/) if it exists, then delete what remains of
   `~/tools/claude`.
2. Remove the now-broken project links, for example `~/_/main/.claude` and
   `~/work/notes/personal-work/.claude`, and `~/.claude/skills` if it is a link.
   Keep anything inside them that is not a link into `~/tools`, such as `.trash`
   and `synced`, and put it back after the bootstrap runs.
3. Run both bootstraps, then `lemonaid skills install` to restore the per-machine
   skill links.

Add shared skills in their global or project scope, then rerun the appropriate
bootstrap. Keep harness invocation metadata beside the shared skill when needed;
for example, [extract-principle](_shared/global/skills/extract-principle/) preserves
explicit-only invocation for both harnesses.
