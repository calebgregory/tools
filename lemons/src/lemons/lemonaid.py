"""Install our additions to lemonaid's home, `~/.lemons`, such as overlays on its packaged skills.

Each file under `lemons/lemonaid/skills/` is linked at the same path under `<lemonaid home>/skills/`.
We own only links that point into `lemons/lemonaid/`; a link or file a user put in lemonaid's home
by hand is theirs, wherever it points, and we refuse to replace it. lemonaid reads an overlay only
when it renders a skill, so after linking we render each skill whose additions we linked or removed.
"""

import os
import shutil
import subprocess
from pathlib import Path

from tools.env import require_env

from lemons import install as installing
from lemons import links


def _source() -> Path:
    return links.LEMONS_DIR / "lemonaid" / "skills"


def _skills_home() -> Path:
    # Read the override exactly as lemonaid does, so we link where it renders from.
    override = os.environ.get("LEMONAID_LEMONS_DIR")
    return (Path(override) if override else Path.home() / ".lemons") / "skills"


def _points_into_source(link: Path) -> bool:
    return Path(os.path.normpath(link.parent / link.readlink())).is_relative_to(_source())


def _owned_stale_links(skills_home: Path, managed: set[Path]) -> tuple[Path, ...]:
    if not skills_home.is_dir():
        return ()
    return tuple(
        entry
        for directory, _, files in sorted(os.walk(skills_home))
        for entry in (Path(directory) / name for name in sorted(files))
        if entry.is_symlink() and entry not in managed and _points_into_source(entry)
    )


def plan() -> links.Plan:
    skills_home = _skills_home()
    linked = tuple(links.adapter_links(_source(), skills_home))
    for link in linked:
        if link.target.is_symlink() and not _points_into_source(link.target):
            raise FileExistsError(
                f"{link.target} links to {link.target.readlink()}, not into {_source()}; "
                "merge it into the source or move it aside before rerunning"
            )
    return links.Plan(linked, stale_links=_owned_stale_links(skills_home, {link.target for link in linked}))


def _skill_name(target: Path) -> str:
    return target.relative_to(_skills_home()).parts[0]


def _render_skills(names: list[str]) -> int:
    if not names:
        return 0
    command = ["lemonaid", "skills", "install", *names]
    if shutil.which("lemonaid") is None:
        print(f"⚠ no lemonaid on PATH; run `{' '.join(command)}` once it is installed")
        return 1
    print(f"→ {' '.join(command)}")
    try:
        returncode = subprocess.run(command, check=False).returncode
    except OSError as error:  # a launcher that can't start, such as one whose interpreter is gone
        print(f"⚠ could not run lemonaid: {error}")
        return 127
    if returncode != 0:
        print(f"⚠ lemonaid skills install exited {returncode}")
    return returncode


def install() -> int:
    """Link our additions, then render the skills whose additions we linked or removed, and no
    others, so we never install a skill nobody chose. Returns the installer's exit status.

    If rendering fails, the links we removed are put back, dangling, so the next run finds them
    stale again and retries the render that would drop their text from the skill.
    """
    config = require_env().lemons
    applied = plan()
    installing.validate_plan(applied, config)
    removed = {link: link.readlink() for link in applied.stale_links}

    installing.apply(applied)
    names = sorted({_skill_name(link.target) for link in applied.links} | {_skill_name(p) for p in removed})
    status = _render_skills(names)

    if status != 0:
        for link, source in removed.items():
            print(f"⚠ restoring {link} → {source}, so the next run renders it again")
            link.symlink_to(source)
    return status
