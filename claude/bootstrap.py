#!/usr/bin/env -S uv run python
"""
Symlinks Claude configs into place. Run after cloning ~/tools on a new machine.

- Per-project configs: symlinked based on .env.toml [claude.project-targets]
- Global config (global/): symlinked into ~/.claude/

Note: any project .claude/'s that have their own .git/-tracking are NOT managed here.
Those live in-project (with own git repo) — see README.md for rationale.
"""

import typing as ty
from pathlib import Path

from tools.env import ClaudeConfig, require_env

_CONFIGS_DIR = Path(__file__).parent
_CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"

#
# .claude project symlinking
#


def _ensure_claude_suffix(path: Path) -> Path:
    return path if path.name == ".claude" else path / ".claude"


def _derive_projects_symlink_src_onto_target(claude_config: ClaudeConfig) -> dict[Path, Path]:
    src_onto_target = {}
    for dir_name, target_path in claude_config.project_targets.items():
        src = _CONFIGS_DIR / dir_name
        target = _ensure_claude_suffix(target_path)
        src_onto_target[src] = target

    exceptions = []
    for src in src_onto_target.keys():
        try:
            assert src.exists() and src.is_dir(), (
                f"Unknown src '{src}' found in .env.toml but does not exist or is not dir"
            )
        except AssertionError as exc:
            exceptions.append(exc)
    if exceptions:
        raise ExceptionGroup("invalid .env.toml [claude.project-targets] config", exceptions)

    return src_onto_target


def _symlink(src: Path, target: Path) -> None:
    if target.is_symlink():
        resolved = target.resolve()
        if resolved == src:
            print(f"✓ {target} already linked → {src}")
            return
        print(f"⚠ {target} linked to wrong src: {resolved}; relinking...")
        target.unlink()

    if target.is_dir():
        print(f"⚠ {target} exists as a real directory — move contents to {src} first, then re-run")
        return

    target.symlink_to(src)
    print(f"→ linked {target} → {src}")


def _link_project_config(src: Path, target: Path) -> None:
    if not src.is_dir():
        print(f"✗ source missing: {src}")
        return
    _symlink(src, target)


#
# auto-memory symlinking
#
# Claude Code's auto-memory dir lives at `~/.claude/projects/<key>/memory/`
# where `<key>` is derived by Claude Code from the project's path (slashes
# replaced with dashes, leading dash). This is machine-local by default;
# we symlink it into our version-controlled config so memory survives a
# fresh checkout on a new machine.


def _auto_memory_key(project_path: Path) -> str:
    """Derive the auto-memory key from an absolute project path.

    Mirrors Claude Code's transform: replace `/` and `.` with `-`.
    Example: `/foo/bar/.baz` -> `-foo-bar--baz` (the `.` AND the preceding
    `/` each become a `-`, yielding `--`).
    """
    resolved = project_path.resolve()
    assert resolved.is_absolute(), f"expected absolute path, got {project_path}"
    return str(resolved).replace("/", "-").replace(".", "-")


def _derive_memory_symlink_src_onto_target(claude_config: ClaudeConfig) -> dict[Path, Path]:
    src_onto_target = {}
    for dir_name, target_path in claude_config.project_targets.items():
        src_memory = _CONFIGS_DIR / dir_name / "memory"
        if not src_memory.is_dir():
            continue
        auto_memory_path = claude_config.auto_memory_paths.get(dir_name, target_path)
        key = _auto_memory_key(auto_memory_path)
        target_memory = _CLAUDE_PROJECTS_DIR / key / "memory"
        src_onto_target[src_memory] = target_memory
    return src_onto_target


def _link_memory(src: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    _symlink(src, target)


#
# global ~/.claude config
#

_GLOBAL_CONFIG_FILES = ("CLAUDE.md", "settings.json", "settings.local.json", "rules", "skills")


def _make_global_symlink_src_onto_target(
    global_config_files: ty.Iterable[str] = _GLOBAL_CONFIG_FILES,
) -> dict[Path, Path]:
    return {
        _CONFIGS_DIR / "global" / file_name: Path.home() / ".claude" / file_name
        for file_name in global_config_files
    }


def _link_global_config(src: Path, target: Path) -> None:
    if not src.exists():
        print(f"✗ source missing: {src}")
        return

    _symlink(src, target)


def cli() -> None:
    claude_config = require_env().claude

    for src, target in _derive_projects_symlink_src_onto_target(claude_config).items():
        _link_project_config(src, target)

    for src, target in _derive_memory_symlink_src_onto_target(claude_config).items():
        _link_memory(src, target)

    for src, target in _make_global_symlink_src_onto_target(_GLOBAL_CONFIG_FILES).items():
        _link_global_config(src, target)


if __name__ == "__main__":
    cli()
