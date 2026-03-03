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


def apply_hunks(
    dest_lines: list[str],
    source_lines: list[str],
    approved: list[bool],
) -> list[str]:
    """Build merged output by applying only approved hunks.

    Uses SequenceMatcher.get_grouped_opcodes to produce hunk-aligned groups
    that correspond 1:1 with unified diff hunks.  For each group, selects
    source lines (if approved) or dest lines (if not) for non-equal ops.
    """
    sm = difflib.SequenceMatcher(None, dest_lines, source_lines)
    groups = list(sm.get_grouped_opcodes())

    if len(groups) != len(approved):
        raise ValueError(f"expected {len(groups)} approval flags, got {len(approved)}")

    out: list[str] = []
    last_dest_pos = 0

    for group, use_source in zip(groups, approved):
        # fill gap of equal lines between previous group and this one
        group_start = group[0][1]
        out.extend(dest_lines[last_dest_pos:group_start])

        for tag, i1, i2, j1, j2 in group:
            if tag == "equal":
                out.extend(dest_lines[i1:i2])
            elif use_source:
                out.extend(source_lines[j1:j2])
            else:
                out.extend(dest_lines[i1:i2])

        last_dest_pos = group[-1][2]

    # trailing equal lines after last group
    out.extend(dest_lines[last_dest_pos:])
    return out
