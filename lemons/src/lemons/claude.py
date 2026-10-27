"""Links for Claude Code: global adapter, rules, skills, project adapters, and shared memory."""

import os
from pathlib import Path

from tools.env import LemonsConfig

from lemons import links
from lemons.links import Link


def _claude_home() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))).expanduser()


def _memory_key(project: Path) -> str:
    """Claude Code's key for a project's auto-memory directory under `~/.claude/projects`."""
    return str(project.resolve()).replace("/", "-").replace(".", "-")


def _global_links(claude_home: Path) -> list[Link]:
    adapter = links.LEMONS_DIR / "claude" / "global"
    return [
        *(
            Link(adapter / name, claude_home / name)
            for name in ("CLAUDE.md", "settings.json", "settings.local.json", "rules")
            if (adapter / name).exists()
        ),
        *links.skill_links(links.SHARED_DIR / "global" / "skills", claude_home / "skills"),
    ]


def _project_links(name: str, target: Path, config: LemonsConfig, claude_home: Path) -> list[Link]:
    project = links.project_root(target)
    shared = links.SHARED_DIR / name
    destination = project / ".claude"
    project_links = [
        *links.adapter_links(links.LEMONS_DIR / "claude" / name, destination),
        *(
            Link(style, destination / "output-styles" / style.name)
            for style in sorted((shared / "output-styles").glob("*.md"))
        ),
        *links.skill_links(shared / "skills", destination / "skills"),
    ]
    if (shared / "memory").is_dir():
        memory_key = _memory_key(config.auto_memory_paths.get(name, project))
        project_links += [
            Link(shared / "memory", destination / "memory"),
            Link(shared / "memory", claude_home / "projects" / memory_key / "memory"),
        ]
    return project_links


def _auto_memory_key_warning(
    name: str, target: Path, config: LemonsConfig, claude_home: Path
) -> str | None:
    """Earlier bootstraps keyed auto-memory by a `.claude` target rather than by its project root."""
    if target.name != ".claude" or name in config.auto_memory_paths:
        return None
    if not (links.SHARED_DIR / name / "memory").is_dir():
        return None
    old_key = _memory_key(target)
    old_link = claude_home / "projects" / old_key / "memory"
    if not old_link.is_symlink():
        return None
    new_key = _memory_key(links.project_root(target))
    return f"Auto-memory key changes from {old_key} to {new_key}; the existing link {old_link} is retained"


def plan(config: LemonsConfig) -> links.Plan:
    claude_home = _claude_home()
    projects = config.project_targets.items()
    all_links = [
        *_global_links(claude_home),
        *(link for name, target in projects for link in _project_links(name, target, config, claude_home)),
    ]
    warnings = [
        warning
        for name, target in projects
        if (warning := _auto_memory_key_warning(name, target, config, claude_home))
    ]
    roots = [claude_home / "skills", *(links.project_root(target) / ".claude" for _, target in projects)]
    return links.migration_plan(all_links, roots, tuple(warnings))
