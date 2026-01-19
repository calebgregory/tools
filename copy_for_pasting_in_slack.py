#!/usr/bin/env python3
"""The script of a man who has HAD ENOUGH!!!!!

Slack Markdown is not like other Markdown...  To get bulletpoint or numbered
lists, you have to double the indentation.  Ugh.  Bold text needs a single *.
Gor.  This script automates that.

Copy whatever Markdown to your system Clipboard, then call this script.  It
will read the text off your clipboard, transform it, then copy the result back
to your clipboard so you can paste it into Slack.  UGGHHHHHHH :((((((."""

import re
import sys

from copy_paste import pbcopy, pbpaste

LIST_RE = re.compile(r"^(\s*)(- |[0-9]\. )")


def _xf_lists(md: str) -> str:
    result_lines = []

    for line in md.split("\n"):
        match = LIST_RE.search(line)
        if not match:
            result_lines.append(line)
            continue

        leading_whitespace = match.group(1)
        list_signifier = match.group(2)
        line_with_double_indentation = (
            (leading_whitespace * 2) + list_signifier + line[match.end() :]
        )
        result_lines.append(line_with_double_indentation)

    return "\n".join(result_lines)


def _xf_bold(md: str) -> str:
    return md.replace("__", "*").replace("**", "*")


def _fmt_markdown_for_slack(md: str) -> str:
    for xf in (
        _xf_bold,
        _xf_lists,
    ):
        md = xf(md)
    return md


def main() -> None:
    input_ = pbpaste() if sys.stdin.isatty() else sys.stdin.read()
    if not input_:
        print("nothing to reformat")
        return

    pbcopy(_fmt_markdown_for_slack(input_))

    print("done")


if __name__ == "__main__":
    main()
