"""Two-way interactive sync between a local source-of-truth directory and a
shared Obsidian vault directory (synced via Relay).

Designed for the case where coworkers can accidentally delete files from the
shared vault.  You maintain your own copy of the files you care about (source)
and periodically sync against the shared directory (dest):

- Files missing from dest are offered for restore (source -> dest).
- Files only in dest are offered for pickup (dest -> source).
- Diverged text files get git-add-patch-style hunk approval; the merged
  result is written to both sides so accepted hunks don't resurface.
- Binary files prompt for a whole-file keep-source / keep-dest choice.

Usage:  sync-vault <source> <dest> [--dry-run]
"""

import shutil
import typing as ty
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from thds.termtool.colorize import colorized

from tools.diff import apply_hunks, colorize_hunk, diff, hunks

_RED = colorized(fg="red")
_GREEN = colorized(fg="green")
_YELLOW = colorized(fg="yellow")
_BLUE = colorized(fg="blue")
_DIM = colorized(fg="gray")


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

DifferenceKind = ty.Literal["source_only", "dest_only", "diverged", "identical"]


class SyncAction(ty.NamedTuple):
    rel: Path
    kind: DifferenceKind
    source: Path
    dest: Path


SyncActionPerformed = ty.Literal["copied_to_dest", "copied_to_source", "merged", "skipped"]


@dataclass
class SyncSummary:
    copied_to_dest: int = 0
    copied_to_source: int = 0
    merged: int = 0
    skipped: int = 0


# ---------------------------------------------------------------------------
# Pure / read-only helpers
# ---------------------------------------------------------------------------


def _is_hidden(rel: Path) -> bool:
    return any(part.startswith(".") for part in rel.parts)


def _discover_files(root: Path) -> dict[Path, Path]:
    return {
        p.relative_to(root): p
        for p in root.rglob("*")
        if p.is_file() and not _is_hidden(p.relative_to(root))
    }


def _is_binary(path: Path) -> bool:
    return b"\x00" in path.read_bytes()[:8192]


def _files_identical(a: Path, b: Path) -> bool:
    return a.read_bytes() == b.read_bytes()


def _classify(
    source_files: dict[Path, Path],
    dest_files: dict[Path, Path],
    source_root: Path,
    dest_root: Path,
) -> list[SyncAction]:
    actions: list[SyncAction] = []
    for rel in sorted(set(source_files) | set(dest_files)):
        src = source_files.get(rel)
        dst = dest_files.get(rel)
        if src and not dst:
            actions.append(SyncAction(rel, "source_only", src, dest_root / rel))
        elif dst and not src:
            actions.append(SyncAction(rel, "dest_only", source_root / rel, dst))
        elif src and dst:
            kind: DifferenceKind = "identical" if _files_identical(src, dst) else "diverged"
            actions.append(SyncAction(rel, kind, src, dst))
    return actions


def _binary_summary(source: Path, dest: Path) -> str:
    s_stat, d_stat = source.stat(), dest.stat()

    def fmt(ts: float) -> str:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

    return "\n".join(
        [
            _YELLOW(f"  binary file: {source.name}"),
            f"  source: {s_stat.st_size:,} bytes, modified {fmt(s_stat.st_mtime)}",
            f"  dest:   {d_stat.st_size:,} bytes, modified {fmt(d_stat.st_mtime)}",
        ]
    )


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _write_to_both(text: str, *paths: Path) -> None:
    for p in paths:
        p.write_text(text)


# ---------------------------------------------------------------------------
# Interactive handlers
# ---------------------------------------------------------------------------


def _handle_source_only(action: SyncAction, *, dry_run: bool) -> SyncActionPerformed:
    print(f"\n{_GREEN('+ ' + str(action.rel))}")
    print("  exists in source, missing from dest")
    if dry_run:
        print(_DIM("  [dry-run] would copy source -> dest"))
        return "copied_to_dest"
    response = input(_BLUE("  Copy to dest? [Y/n] ")).strip().lower()
    if response in ("", "y"):
        _copy_file(action.source, action.dest)
        return "copied_to_dest"
    return "skipped"


def _handle_dest_only(action: SyncAction, *, dry_run: bool) -> SyncActionPerformed:
    print(f"\n{_YELLOW('? ' + str(action.rel))}")
    print("  exists in dest, missing from source")
    if dry_run:
        print(_DIM("  [dry-run] would copy dest -> source"))
        return "copied_to_source"
    response = input(_BLUE("  Copy to source? [Y/n] ")).strip().lower()
    if response in ("", "y"):
        _copy_file(action.dest, action.source)
        return "copied_to_source"
    return "skipped"


def _handle_diverged(action: SyncAction, *, dry_run: bool) -> SyncActionPerformed:
    print(f"\n{_RED('~ ' + str(action.rel))}")

    if _is_binary(action.source) or _is_binary(action.dest):
        return _handle_diverged_binary(action, dry_run=dry_run)
    return _handle_diverged_text(action, dry_run=dry_run)


def _handle_diverged_binary(action: SyncAction, *, dry_run: bool) -> SyncActionPerformed:
    print(_binary_summary(action.source, action.dest))
    if dry_run:
        print(_DIM("  [dry-run] would prompt: source / dest / skip"))
        return "skipped"
    response = input(_BLUE("  Keep [s]ource / [d]est / s[k]ip? ")).strip().lower()
    if response in ("", "s"):
        _copy_file(action.source, action.dest)
        return "copied_to_dest"
    elif response == "d":
        _copy_file(action.dest, action.source)
        return "copied_to_source"
    return "skipped"


def _handle_diverged_text(action: SyncAction, *, dry_run: bool) -> SyncActionPerformed:
    d = diff(action.source, action.dest)
    hunk_list = hunks(d)

    if not hunk_list:
        print(_DIM("  (no text diff)"))
        return "skipped"

    if dry_run:
        for h in hunk_list:
            print(colorize_hunk(h))
        print(_DIM(f"  [dry-run] {len(hunk_list)} hunk(s) would be prompted"))
        return "merged"

    dest_lines = action.dest.read_text().splitlines(keepends=True)
    source_lines = action.source.read_text().splitlines(keepends=True)
    approved: list[bool] = []
    accept_all = False

    for i, h in enumerate(hunk_list):
        print(colorize_hunk(h))

        if accept_all:
            approved.append(True)
            continue

        prompt = _BLUE(f"  hunk {i + 1}/{len(hunk_list)} — [y]es / [n]o / [a]ll / [q]uit? ")
        response = input(prompt).strip().lower()
        if response in ("", "y"):
            approved.append(True)
        elif response == "a":
            approved.append(True)
            accept_all = True
        elif response == "q":
            approved.append(False)
            approved.extend(False for _ in range(len(hunk_list) - i - 1))
            break
        else:
            approved.append(False)

    if not any(approved):
        return "skipped"

    merged = apply_hunks(dest_lines, source_lines, approved)
    merged_text = "".join(merged)
    _write_to_both(merged_text, action.source, action.dest)
    return "merged"


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

_HANDLERS: dict[DifferenceKind, ty.Callable[[SyncAction, bool], SyncActionPerformed]] = {
    "source_only": lambda a, dr: _handle_source_only(a, dry_run=dr),
    "dest_only": lambda a, dr: _handle_dest_only(a, dry_run=dr),
    "diverged": lambda a, dr: _handle_diverged(a, dry_run=dr),
}


def sync(source: Path, dest: Path, *, dry_run: bool = False) -> SyncSummary:
    source_files = _discover_files(source)
    dest_files = _discover_files(dest)
    actions = _classify(source_files, dest_files, source, dest)

    identical = [a for a in actions if a.kind == "identical"]
    actionable = [a for a in actions if a.kind != "identical"]

    if not actionable:
        print(_GREEN("Everything in sync."))
        return SyncSummary(0, 0, 0, len(identical))

    print(f"Found {len(actionable)} file(s) to review ({len(identical)} identical, skipped)\n")

    summary = SyncSummary()
    for action in actionable:
        handler = _HANDLERS[action.kind]
        result = handler(action, dry_run)
        match result:
            case "copied_to_source":
                summary.copied_to_source += 1
            case "copied_to_dest":
                summary.copied_to_dest += 1
            case "merged":
                summary.merged += 1
            case "skipped":
                summary.skipped += 1

    _print_summary(summary)
    return summary


def _print_summary(s: SyncSummary) -> None:
    lines = [
        "",
        "=" * 40,
        f"  Copied to dest:   {s.copied_to_dest}",
        f"  Copied to source: {s.copied_to_source}",
        f"  Merged:           {s.merged}",
        f"  Skipped:          {s.skipped}",
    ]
    print("\n".join(lines))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Two-way sync between a source-of-truth directory and a shared directory."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("dest", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    for label, path in [("source", args.source), ("dest", args.dest)]:
        if not path.is_dir():
            parser.error(f"{label} directory does not exist: {path}")

    sync(args.source, args.dest, dry_run=args.dry_run)


if __name__ == "__main__":
    cli()
