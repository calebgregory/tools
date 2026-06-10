import difflib
import typing as ty
from pathlib import Path

from thds.termtool.colorize import colorized

_RED = colorized(fg="red")
_GREEN = colorized(fg="green")
_BLUE = colorized(fg="blue")
_DIM = colorized(fg="gray")


Diff = list[str]


def diff(v1: Path, v2: Path) -> Diff:
    lines = difflib.unified_diff(
        v2.read_text().splitlines(keepends=True),
        v1.read_text().splitlines(keepends=True),
        fromfile=str(v2),
        tofile=str(v1),
    )
    return list(lines)


def _colorize_diff_line(line: str) -> str:
    for char, color in {"+": _GREEN, "-": _RED}.items():
        if line.startswith(char):
            return color(line)
    return line


def colorize(d: Diff) -> str:
    return "".join(map(_colorize_diff_line, d))


# ---------------------------------------------------------------------------
# Hunk parsing and selective application
# ---------------------------------------------------------------------------


class Hunk(ty.NamedTuple):
    header: str
    diff_lines: list[str]


def hunks(d: Diff) -> list[Hunk]:
    """Split a unified diff into hunks (one per @@ header)."""
    result: list[Hunk] = []
    current_header: str | None = None
    current_lines: list[str] = []

    for line in d:
        if line.startswith("@@"):
            if current_header is not None:
                result.append(Hunk(current_header, current_lines))
            current_header = line
            current_lines = []
        elif current_header is not None:
            current_lines.append(line)
        # skip --- / +++ / other preamble lines

    if current_header is not None:
        result.append(Hunk(current_header, current_lines))

    return result


def colorize_hunk(hunk: Hunk) -> str:
    header = _BLUE(hunk.header)
    body = "".join(map(_colorize_diff_line, hunk.diff_lines))
    return header + body


HunkChoice = ty.Literal["source", "dest", "skip"]


class MergedSides(ty.NamedTuple):
    """Independent post-merge contents for each side.

    `source` and `dest` differ only in regions whose hunk was skipped; for
    every resolved hunk both sides carry the chosen version, so they converge
    there.
    """

    source: list[str]
    dest: list[str]


def apply_hunks(
    dest_lines: list[str],
    source_lines: list[str],
    choices: list[HunkChoice],
) -> MergedSides:
    """Build per-side merged output from a three-way choice per hunk.

    Uses SequenceMatcher.get_grouped_opcodes to produce hunk-aligned groups
    that correspond 1:1 with unified diff hunks.  For each group's non-equal
    ops the choice decides what both sides receive:

      "source"  both sides take source's version (source -> dest)
      "dest"    both sides take dest's version   (dest -> source)
      "skip"    each side keeps its own version  (region stays diverged)
    """
    sm = difflib.SequenceMatcher(None, dest_lines, source_lines)
    groups = list(sm.get_grouped_opcodes())

    if len(groups) != len(choices):
        raise ValueError(f"expected {len(groups)} choice(s), got {len(choices)}")

    new_dest: list[str] = []
    new_source: list[str] = []
    last_dest_pos = 0
    last_source_pos = 0

    for group, choice in zip(groups, choices):
        # fill gap of equal lines between previous group and this one
        new_dest.extend(dest_lines[last_dest_pos : group[0][1]])
        new_source.extend(source_lines[last_source_pos : group[0][3]])

        for tag, i1, i2, j1, j2 in group:
            if tag == "equal":
                new_dest.extend(dest_lines[i1:i2])
                new_source.extend(source_lines[j1:j2])
            elif choice == "source":
                new_dest.extend(source_lines[j1:j2])
                new_source.extend(source_lines[j1:j2])
            elif choice == "dest":
                new_dest.extend(dest_lines[i1:i2])
                new_source.extend(dest_lines[i1:i2])
            else:  # skip: each side keeps its own
                new_dest.extend(dest_lines[i1:i2])
                new_source.extend(source_lines[j1:j2])

        last_dest_pos = group[-1][2]
        last_source_pos = group[-1][4]

    # trailing equal lines after last group
    new_dest.extend(dest_lines[last_dest_pos:])
    new_source.extend(source_lines[last_source_pos:])
    return MergedSides(source=new_source, dest=new_dest)
