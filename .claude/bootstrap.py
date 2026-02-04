#!/usr/bin/env -S uv run python
"""
Symlinks Claude configs into place. Run after cloning ~/tools on a new machine.

- Per-project configs: symlinked based on .env.toml [claude.project-targets]
- Global config (global/): symlinked into ~/.claude/

Note: any project .claude/'s that have their own .git/-tracking are NOT managed here.
Those live in-project (with own git repo) — see README.md for rationale.
"""

import shutil
import tomllib
import typing as ty
from dataclasses import dataclass, field
from pathlib import Path

_CONFIGS_DIR = Path(__file__).parent
_PROJECT_ROOT = _CONFIGS_DIR.parent
_ENV_TOML = _PROJECT_ROOT / ".env.toml"
_ENV_TEMPLATE = _PROJECT_ROOT / ".env.template.toml"


#
# .env.toml - TODO: put this into its own module if it gets more complex
#


@dataclass
class ClaudeConfig:
    project_targets: dict[str, str] = field(default_factory=dict)


@dataclass
class EnvTomlConfig:
    computer_name: str = ""
    claude: ClaudeConfig = field(default_factory=ClaudeConfig)


def load_env() -> EnvTomlConfig | None:
    if not _ENV_TOML.exists():
        return None
    with _ENV_TOML.open("rb") as f:
        data = tomllib.load(f)

    claude_data = data.get("claude", {})
    claude_config = ClaudeConfig(
        project_targets=claude_data.get("project-targets", {}),
    )
    return EnvTomlConfig(
        computer_name=data.get("computer_name", ""),
        claude=claude_config,
    )


def require_env() -> EnvTomlConfig:
    env = load_env()
    if env is None:
        shutil.copy(_ENV_TEMPLATE, _ENV_TOML)
        raise EnvironmentError(".env.toml did not previously exist; fill it out now and re-run this script")
    return env


#
# .claude project symlinking
#


def _ensure_claude_suffix(path: Path) -> Path:
    return path if path.name == ".claude" else path / ".claude"


def _derive_projects_symlink_src_onto_target(claude_config: ClaudeConfig) -> dict[Path, Path]:
    src_onto_target = {}
    for dir_name, target_str in claude_config.project_targets.items():
        if not target_str:
            continue
        src = _CONFIGS_DIR / dir_name
        target = _ensure_claude_suffix(Path(target_str).expanduser())
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
        print(f"✓ {target} already linked → {target.resolve()}")
    elif target.is_dir():
        print(f"⚠ {target} exists as a real directory — move contents to {src} first, then re-run")
    else:
        target.symlink_to(src)
        print(f"→ linked {target} → {src}")


def _link_project_config(src: Path, target: Path) -> None:
    if not src.is_dir():
        print(f"✗ source missing: {src}")
        return
    _symlink(src, target)


#
# global ~/.claude config
#

_GLOBAL_CONFIG_FILES = ("CLAUDE.md", "settings.json", "rules")


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
    for src, target in _derive_projects_symlink_src_onto_target(require_env().claude).items():
        _link_project_config(src, target)

    for src, target in _make_global_symlink_src_onto_target(_GLOBAL_CONFIG_FILES).items():
        _link_global_config(src, target)


if __name__ == "__main__":
    cli()
