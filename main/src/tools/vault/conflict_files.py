import re
import typing as ty
from pathlib import Path

from thds.termtool.colorize import colorized

from tools import diff
from tools.env import require_env

_YELLOW = colorized(fg="yellow")
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


def find_and_prompt_to_delete_conflict_files(vault_root: Path, *, force: bool = False) -> int:
    count = 0
    for src, conflict in map(_match_conflict_file_with_source, _find_conflict_files(vault_root)):
        if force:
            conflict.unlink()
            count += 1
            continue

        diff_ = diff.colorize(diff.diff(src, conflict))
        if not diff_:
            print(f"- {src} ({_YELLOW('no changes')})")
            continue

        print(diff_)
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
