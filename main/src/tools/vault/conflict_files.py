import difflib
import re
import typing as ty
from pathlib import Path

from thds.termtool.colorize import colorized

from tools.env import require_env

_RED = colorized(fg="red")
_YELLOW = colorized(fg="yellow")
_GREEN = colorized(fg="green")
_BLUE = colorized(fg="blue")


def _find_conflict_files(root: Path) -> ty.Iterator[Path]:
    yield from root.rglob("* (Conflicted copy *")


class Conflict(ty.NamedTuple):
    source: Path
    conflict: Path


def _match_conflict_file_with_source(conflict_file: Path) -> Conflict:
    conflict_re = r" \(Conflicted copy .+\)\.md$"
    source_file = conflict_file.parent / re.sub(conflict_re, ".md", conflict_file.name)
    assert source_file.exists(), f"conflict_file {conflict_file} has no source to match"
    return Conflict(source_file, conflict_file)


def _colorize_diff_line(line: str) -> str:
    for char, color in {"+": _GREEN, "-": _RED}.items():
        if line.startswith(char):
            return color(line)
    return line


def _colored_diff(v1: Path, v2: Path) -> str:
    lines = difflib.unified_diff(
        v2.read_text().splitlines(keepends=True),
        v1.read_text().splitlines(keepends=True),
        fromfile=str(v2),
        tofile=str(v1),
    )
    return "".join(map(_colorize_diff_line, lines))


def find_and_prompt_to_delete_conflict_files(vault_root: Path, *, force: bool = False) -> int:
    count = 0
    for src, conflict in map(_match_conflict_file_with_source, _find_conflict_files(vault_root)):
        if force:
            conflict.unlink()
            count += 1
            continue

        diff = _colored_diff(src, conflict)
        if not diff:
            print(f"- {src} ({_YELLOW('no changes')})")
            continue

        print(diff)
        response = input(_BLUE(f"Delete {conflict.name}? [y/N] ")).strip().lower()
        if response == "y":
            conflict.unlink()
            count += 1
        else:
            print(f"  skipped {conflict.name}")
    print(f"deleted {count} conflict files")
    return count


def cli() -> None:
    vault_root = require_env().vault.main.root
    assert vault_root
    find_and_prompt_to_delete_conflict_files(vault_root)


if __name__ == "__main__":
    cli()
