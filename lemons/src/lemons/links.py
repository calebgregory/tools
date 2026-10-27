"""Links a bootstrap installs, and the plan that reconciles them with an earlier install."""

import os
import typing as ty
from pathlib import Path

LEMONS_DIR = Path(__file__).resolve().parents[2]
SHARED_DIR = LEMONS_DIR / "_shared"
# Harness-owned skill directories; earlier installs left them inside the shared tree.
_RUNTIME_ENTRIES = frozenset({".trash", "synced"})
_UNINSTALLED_ADAPTER_FILES = frozenset({"README.md", ".gitignore", ".DS_Store"})


class Link(ty.NamedTuple):
    source: Path
    target: Path


class Move(ty.NamedTuple):
    source: Path
    target: Path


class Plan(ty.NamedTuple):
    links: tuple[Link, ...]
    legacy_directory_links: tuple[Path, ...] = ()
    moves: tuple[Move, ...] = ()
    stale_links: tuple[Path, ...] = ()
    warnings: tuple[str, ...] = ()


def project_root(target: Path) -> Path:
    return target.parent if target.name == ".claude" else target


def skill_links(source: Path, target: Path) -> list[Link]:
    if not source.is_dir():
        return []
    return [
        Link(skill, target / skill.name)
        for skill in sorted(source.iterdir())
        if not skill.name.startswith(".") and skill.is_dir() and (skill / "SKILL.md").is_file()
    ]


def adapter_links(adapter: Path, destination: Path) -> list[Link]:
    # Link files individually so the harness writes its runtime files to a local directory.
    return [
        Link(path, destination / path.relative_to(adapter))
        for path in sorted(adapter.rglob("*"))
        if (path.is_symlink() or path.is_file())
        and path.name not in _UNINSTALLED_ADAPTER_FILES
        and _RUNTIME_ENTRIES.isdisjoint(path.relative_to(adapter).parts)
    ]


#
# Migration of earlier installs
#


def _legacy_directory_links(roots: list[Path], link_directories: set[Path]) -> tuple[Path, ...]:
    """Directories that an earlier install linked whole into the repository, outermost only."""
    candidates = {*roots, *(d for d in link_directories if any(d.is_relative_to(r) for r in roots))}
    legacy: list[Path] = []
    for directory in sorted(candidates):  # a directory sorts before its descendants
        if directory.is_symlink() and not any(directory.is_relative_to(parent) for parent in legacy):
            if not directory.resolve().is_dir():
                raise FileNotFoundError(
                    f"Broken legacy directory link: {directory}; remove it before rerunning"
                )
            legacy.append(directory)
    return tuple(legacy)


def _moves_out_of_legacy_directory(source: Path, destination: Path, managed: set[Path]) -> list[Move]:
    """Entries of a legacy directory that keep their place once it becomes a local directory."""
    moves: list[Move] = []
    for entry in sorted(source.iterdir()):
        target = destination / entry.name
        if target in managed or entry.name == ".DS_Store":
            continue
        if entry.is_dir() and any(path.is_relative_to(target) for path in managed):
            moves += _moves_out_of_legacy_directory(entry.resolve(), target, managed)
        elif entry.name in _RUNTIME_ENTRIES:
            # Move the runtime data itself, not an alias into the shared tree.
            moves.append(Move(entry.resolve(), target))
        elif entry.is_symlink() or not entry.is_relative_to(LEMONS_DIR.parent):
            moves.append(Move(entry, target))
        elif entry.name not in _UNINSTALLED_ADAPTER_FILES:
            raise FileExistsError(
                f"{entry} is in the repository but no link manages it; move or delete it before rerunning"
            )
    return moves


def _installed_directories(
    roots: list[Path], link_directories: set[Path], legacy: tuple[Path, ...]
) -> set[Path]:
    """Directories the bootstrap owns links in: where it links now and wherever an earlier install did."""
    walked = {
        Path(directory)
        for root in roots
        if root.is_dir() and not root.is_symlink()
        for directory, _, _ in os.walk(root)
        if _RUNTIME_ENTRIES.isdisjoint(Path(directory).relative_to(root).parts)
    }
    # A legacy directory link still resolves into the repository, so its entries are not stale.
    return {
        d for d in {*link_directories, *walked} if not any(d.is_relative_to(parent) for parent in legacy)
    }


def _points_into_lemons(link: Path) -> bool:
    return Path(os.path.normpath(link.parent / link.readlink())).is_relative_to(LEMONS_DIR)


def _stale_links(directories: set[Path], managed: set[Path]) -> tuple[Path, ...]:
    return tuple(
        entry
        for directory in sorted(directories)
        if directory.is_dir()
        for entry in sorted(directory.iterdir())
        if entry.is_symlink() and entry not in managed and _points_into_lemons(entry)
    )


def migration_plan(links: list[Link], roots: list[Path], warnings: tuple[str, ...] = ()) -> Plan:
    """Reconcile the links with whatever an earlier install left under the roots."""
    deduplicated = tuple({link.target: link for link in links}.values())
    managed = {link.target for link in deduplicated}
    link_directories = {link.target.parent for link in deduplicated}
    legacy = _legacy_directory_links(roots, link_directories)
    moves = [
        move
        for directory in legacy
        for move in _moves_out_of_legacy_directory(directory.resolve(), directory, managed)
    ]
    stale = _stale_links(_installed_directories(roots, link_directories, legacy), managed | set(legacy))
    return Plan(deduplicated, legacy, tuple(moves), stale, warnings)
