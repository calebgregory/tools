#!/usr/bin/env -S uv run python
"""
how much did i walk today?

demo:

```
$ cal
   December 2025
Su Mo Tu We Th Fr Sa
    1  2  3  4  5  6
 7  8  9 10 11 12 13
14 15 16 17 18 19 20
21 22 23 24 25 26 27
28 29 30 31

$ cat <<EOM > my_log_file.md  # example of log_file format
2025-12-01: 1.5 3
a note to self...
2025-12-08: 2
EOM

$ ./walked.py my_log_file.md  # slimmed-down output is printed to the console
2025-12-01: (04.50)  1.50 3.00
---week---:  4.50
2025-12-08: (02.00)  2.00
---week---:  2.00

$ cat my_log_file.md          # the script overwrites the input file with printed sums for day and week
2025-12-01: (04.50)  1.50 3.00
a note to self...
---week---:  4.50
2025-12-08: (02.00)  2.00
---week---:  2.00
```

this script assumes the input log_file abides by a particular format, and it has
certain limitations.

the format:

```
2025-12-25: 0.5 3.11
# ^ this will be parsed as a daily entry; multiple entries per day are
# supported, as we often walk multiple times per day

some random line
# ^ this will just be passed through and re-printed

2025-12-26: 2.0
# ^ another entry
```

sums for the day and for the week will be generated and printed for you.  you
don't need to edit these.

the limitations:

- our script pretty much assumes you are writing entries in order by date
ascending - the later the date, the later the line.  the behavior when you are
_not_ doing that is undefined.
"""

import math
import re
import typing as ty
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path


@dataclass
class _Entry:
    date: date
    total: float
    values: list[float]
    unparsable: list[str]


_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}:\s+.+$"


def _is_entry(line: str) -> bool:
    return bool(re.match(_DATE_PATTERN, line))


def _parse_entry(line: str) -> _Entry | None:
    if not _is_entry(line):
        return None

    date_s, rest = line.strip().split(":")
    date_ = date.fromisoformat(date_s.strip())

    vals, unparsable = [], []
    for m in rest.strip().split():
        try:
            vals.append(float(m))
        except ValueError:
            unparsable.append(m)

    total = sum(vals)

    return _Entry(date_, total, vals, unparsable)


def _fmt_entry(entry: _Entry) -> str:
    value_strs = (f"{v:.2f}" for v in entry.values)
    return f"{entry.date.isoformat()}: ({entry.total:0>5.2f})  {' '.join(value_strs)}"


@dataclass
class _Week:
    start: date
    end: date
    total: float = 0.0


_WEEK_PATTERN = r"^---week---:\s+(\d+).*$"


def _is_week(line: str) -> bool:
    return bool(re.match(_WEEK_PATTERN, line))


def _yield_weeks_in_range(start: date, end: date) -> ty.Iterator[_Week]:
    first_week_start = start - timedelta(days=start.weekday())
    first_week = _Week(first_week_start, first_week_start + timedelta(days=6))
    yield first_week

    num_weeks = math.ceil((end - first_week_start).days / 7)
    for n in range(7, 7 * num_weeks + 1, 7):
        yield _Week(first_week_start + timedelta(days=n), first_week_start + timedelta(days=n + 6))


def _total_from_entries(entries: list[_Entry]) -> float:
    return sum(entry.total for entry in entries)


def _yield_weeks(entries: ty.Iterable[_Entry]) -> ty.Iterator[_Week]:
    sorted_entries = sorted(entries, key=lambda e: e.date)
    first, last = sorted_entries[0], sorted_entries[-1]

    for week in _yield_weeks_in_range(start=first.date, end=last.date):
        entries = [entry for entry in sorted_entries if week.start <= entry.date <= week.end]
        yield _Week(start=week.start, end=week.end, total=_total_from_entries(entries))


def _fmt_week(week: _Week) -> str:
    return f"---week---:  {week.total:.2f}"


_Line = _Entry | _Week | str


def _parse_lines_in(log_file_text: str) -> list[_Line]:
    lines: list[_Line] = []
    for line in log_file_text.splitlines():
        if entry := _parse_entry(line):
            lines.append(entry)
        elif _is_week(line):
            continue  # omit; we re-generate each time script is run
        else:
            lines.append(line)
    return lines


def _derive_lines_out(lines_in: list[_Line]) -> list[_Line]:
    entries = tuple(line for line in lines_in if isinstance(line, _Entry))
    week_gen = _yield_weeks(entries)
    # we know our weeks overlap with the full range of entries, so we don't
    # worry about handling raised StopIteration exceptions
    week = next(week_gen)

    lines: list[_Line] = []
    for line in lines_in:
        if isinstance(line, str):
            lines.append(line)
            continue
        if isinstance(line, _Week):
            continue

        entry = line
        if week.end < entry.date:
            # we've reached an entry for "next week", append the current week's line
            lines.append(week)
            week = next(week_gen)
            # then move on with the new week's entries
        lines.append(entry)

        if entry == entries[-1]:  # at final entry; append final week's line
            assert week not in lines
            lines.append(week)
    return lines


@dataclass
class _Output:
    log_file: list[str] = field(default_factory=list)
    console: list[str] = field(default_factory=list)

    @property
    def log_file_s(self) -> str:
        txt = "\n".join(self.log_file)
        return txt if txt.endswith("\n") else txt + "\n"

    @property
    def console_s(self) -> str:
        return "\n".join(self.console)


def _print_out(lines_out: list[_Line]) -> _Output:
    out = _Output()
    for line in lines_out:
        if isinstance(line, _Entry):
            fmtd = _fmt_entry(line)
            out.log_file.append(fmtd)
            out.console.append(fmtd)
        elif isinstance(line, _Week):
            fmtd = _fmt_week(line)
            out.log_file.append(fmtd)
            out.console.append(fmtd)
        else:
            out.log_file.append(line)  # retain line
    return out


def main(log_file: Path) -> None:
    output = _print_out(_derive_lines_out(_parse_lines_in(log_file.read_text())))
    print(output.console_s)
    log_file.write_text(output.log_file_s)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", type=Path)
    args = parser.parse_args()

    main(args.log_file)
