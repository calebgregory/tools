"""Links for Codex: global and project adapters, and skills in its native discovery locations."""

import os
from pathlib import Path

from tools.env import LemonsConfig

from lemons import links
from lemons.links import Link


def _project_links(name: str, project: Path) -> list[Link]:
    # Codex reads AGENTS.md from the project root, not from a hidden directory.
    adapter = links.LEMONS_DIR / "codex" / name / "AGENTS.md"
    return [
        *([Link(adapter, project / "AGENTS.md")] if adapter.is_file() else []),
        *links.skill_links(links.SHARED_DIR / name / "skills", project / ".agents" / "skills"),
    ]


def plan(config: LemonsConfig) -> links.Plan:
    home = Path.home()
    codex_home = Path(os.environ.get("CODEX_HOME", str(home / ".codex"))).expanduser()
    # Codex discovers user skills under `~/.agents`, independent of CODEX_HOME.
    global_skills = home / ".agents" / "skills"
    projects = {name: links.project_root(target) for name, target in config.project_targets.items()}
    all_links = [
        Link(links.LEMONS_DIR / "codex" / "AGENTS.md", codex_home / "AGENTS.md"),
        *links.skill_links(links.SHARED_DIR / "global" / "skills", global_skills),
        *(link for name, project in projects.items() for link in _project_links(name, project)),
    ]
    roots = [global_skills, *(project / ".agents" / "skills" for project in projects.values())]
    return links.migration_plan(all_links, roots)
