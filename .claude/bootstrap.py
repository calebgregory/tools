#!/usr/bin/env python
"""
Symlinks per-project .claude/ configs into place.
Run after cloning ~/tools on a new machine.

Global config (~/.claude/) is handled separately by ~/.dotfiles/.claude/bootstrap.sh

Note: any project .claude/'s that have their own .git/-tracking are NOT managed here.
Those live in-project (with own git repo) — see README.md for rationale.
"""

from pathlib import Path

_HOME = Path.home()
_CONFIGS_DIR = Path(__file__).parent

# source dir → symlink location
# Add new projects here:
_LINKS = {
    _CONFIGS_DIR / "vault-main": _HOME / "_/main/.claude",
}


def _link_config(src: Path, target: Path) -> None:
    if not src.is_dir():
        print(f"✗ source missing: {src}")
        return

    if target.is_symlink():
        print(f"✓ {target} already linked → {target.resolve()}")
    elif target.is_dir():
        print(f"⚠ {target} exists as a real directory — move contents to {src} first, then re-run")
    else:
        target.symlink_to(src)
        print(f"→ linked {target} → {src}")


def cli():
    for src, target in _LINKS.items():
        _link_config(src, target)


if __name__ == "__main__":
    cli()
