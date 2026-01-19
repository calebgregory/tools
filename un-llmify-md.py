#!/usr/bin/env -S uv run python
import sys
import typing as ty
from pathlib import Path

from copy_paste import pbcopy, pbpaste

xfs: ty.Final = {
    "* [ ]": "- [ ]",
    "’": "'",
    "“": '"',
    "”": '"',
    "**": "__",
}


def _replace_common_formatting(content: str) -> str:
    for from_, to in xfs.items():
        content = content.replace(from_, to)
    return content


def main(file: Path | None = None) -> None:
    if file:
        file.write_text(_replace_common_formatting(file.read_text()))
        print("done")
        return

    is_atty = sys.stdin.isatty()
    input_ = pbpaste() if is_atty else sys.stdin.read()
    if not input_:
        print("nothing to transform")
        return

    xfed = _replace_common_formatting(input_)
    if is_atty:
        pbcopy(xfed)
        print("done")
    else:
        print(xfed)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", type=Path)
    args = parser.parse_args()

    main(args.file)
