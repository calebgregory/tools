"""Validate a plan against the disk, then apply it."""

import shutil
from pathlib import Path

from lemons import links
from tools.env import LemonsConfig


def validate_plan(plan: links.Plan, config: LemonsConfig) -> None:
    for name, target in config.project_targets.items():
        project = links.project_root(target)
        if not project.is_dir():
            raise FileNotFoundError(f"Project root does not exist: {project}")
        if not (links.SHARED_DIR / name).is_dir():
            raise FileNotFoundError(f"Unknown shared project: {links.SHARED_DIR / name}")
    for source, target in [*plan.links, *plan.moves]:
        if not source.exists() and not source.is_symlink():
            raise FileNotFoundError(f"Source missing: {source}")
        if any(target.is_relative_to(directory) for directory in plan.legacy_directory_links):
            continue
        if target.exists() and not target.is_symlink():
            raise FileExistsError(
                f"{target} already exists; merge it into {source} or move it aside before rerunning"
            )
        for parent in target.parents:
            if parent.exists():
                if not parent.is_dir():
                    raise NotADirectoryError(f"Destination parent is not a directory: {parent}")
                break


def _symlink(source: Path, target: Path) -> None:
    if target.is_symlink():
        # Compare link text: compatibility links may resolve correctly today.
        if target.readlink() == source:
            print(f"✓ {target} already linked → {source}")
            return
        print(f"⚠ {target} linked to {target.readlink()}; relinking → {source}")
        target.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(source, target_is_directory=source.is_dir())
    print(f"→ linked {target} → {source}")


def apply(plan: links.Plan) -> None:
    for warning in plan.warnings:
        print(f"⚠ {warning}")
    for link in plan.stale_links:
        print(f"⚠ removing stale link {link} → {link.readlink()}")
        link.unlink()
    for directory in plan.legacy_directory_links:
        print(f"⚠ Replacing legacy directory link {directory} with a local directory")
        directory.unlink()
        directory.mkdir()
    for source, target in plan.moves:
        print(f"→ moving local runtime entry {source} → {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
    for source, target in plan.links:
        _symlink(source, target)
