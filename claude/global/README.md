# Global Claude Config

Machine-wide Claude Code settings. Contents are symlinked into `~/.claude/` by [`../bootstrap.py`](../bootstrap.py).

## Contents

| File | Purpose |
|------|---------|
| `settings.json` | Global settings: model preference, hooks, statusline config |
| `CLAUDE.md` | Global instructions applied to all Claude sessions |
| `rules/` | Coding standards and preferences |
| `statusline.py` | Custom statusline script (displays session metadata) |

## Setup

Run `./bootstrap.py` from the parent directory after cloning `~/tools` on a new machine.
