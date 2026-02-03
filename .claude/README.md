# Claude Config Management

Per-project `.claude/` directories contain skills, agents, output styles, and project-specific `CLAUDE.md` files. Obsidian Sync ignores hidden directories, so vault-level config needs to live here (git-tracked) and be symlinked into place.

## What lives here

| Directory | Purpose |
|-----------|---------|
| `vault-main/` | Personal task management tools for the Obsidian vault |
| `work-org/` | Work task management (Shape-up, monorepo-aware). Company-specific context lives in project's `CLAUDE.md`. |

Symlink targets are configured in `~/tools/.env.toml` under `[claude.project-targets]`.

## What does NOT live here

| Config | Location | Reason |
|--------|----------|--------|
| `~/.dotfiles/.claude/` | `~/.dotfiles` | Global Claude settings (model, hooks, statusline). Already managed by dotfiles bootstrap. Symlinked to `~/.claude/`. |
| `andrew-and-kayla-wedding/.claude/` | `~/_/main/projects/andrew-and-kayla-wedding/.claude/` | Project-specific tools (ceremony drafting, interview prep, story bank agents). Lives in-project because: (1) it's already git-tracked in its own repo, (2) the skills/agents reference project-relative paths and are tightly coupled to that project's structure, (3) it has its own output style and will be archived with the project when the wedding is done. No benefit to centralizing. |

## Adding a new project

If a new project needs Claude config and isn't independently git-tracked:

1. Create `<project-name>/` here with the config
2. Add `<project-name> = "/path/to/project"` under `[claude.project-targets]` in `~/tools/.env.toml`
3. Run `./bootstrap.py`

If a project IS independently git-tracked (has its own `.git/`), keep `.claude/` in-project — same rationale as the wedding project.

## Bootstrap

Run `./bootstrap.py` after cloning on a new machine.

If `~/tools/.env.toml` doesn't exist, the script copies `.env.template.toml` and exits — fill it out, then re-run.
