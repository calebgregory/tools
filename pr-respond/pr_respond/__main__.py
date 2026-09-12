import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from . import _fetch, _parse, _submit

type _CmdHandler = Callable[[argparse.Namespace], int]


def _cmd_fetch(args: argparse.Namespace) -> int:
    output = Path(args.output) if args.output else None
    try:
        result = _fetch.fetch(args.pr, output)
        print(f"Wrote {result}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _cmd_submit(args: argparse.Namespace) -> int:
    try:
        review = _parse.parse(Path(args.file))
        _submit.submit(review, event=args.event, dry_run=args.dry_run)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _cmd_diff(args: argparse.Namespace) -> int:
    try:
        review = _parse.parse(Path(args.file))
        print(_submit.diff(review, args.event))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pr-respond",
        description="Respond to GitHub PR comments via markdown",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # fetch command
    fetch_parser = subparsers.add_parser(
        "fetch", help="Fetch PR comments into a markdown file"
    )
    fetch_parser.add_argument(
        "pr", help="PR reference (owner/repo#123 or GitHub URL)"
    )
    fetch_parser.add_argument(
        "-o", "--output", help="Output file path (default: pr-<N>-comments.md)"
    )
    fetch_parser.set_defaults(func=_cmd_fetch)

    # submit command
    submit_parser = subparsers.add_parser(
        "submit", help="Submit responses from markdown file"
    )
    submit_parser.add_argument("file", help="Markdown file to submit")
    submit_parser.add_argument(
        "--dry-run", action="store_true", help="Preview without submitting"
    )
    submit_parser.add_argument(
        "--event",
        choices=["COMMENT", "APPROVE", "REQUEST_CHANGES"],
        default="COMMENT",
        help="Review event type (default: COMMENT)",
    )
    submit_parser.set_defaults(func=_cmd_submit)

    # diff command
    diff_parser = subparsers.add_parser(
        "diff", help="Preview what would be submitted"
    )
    diff_parser.add_argument("file", help="Markdown file to preview")
    diff_parser.add_argument(
        "--event",
        choices=["COMMENT", "APPROVE", "REQUEST_CHANGES"],
        default="COMMENT",
        help="Review event type (default: COMMENT)",
    )
    diff_parser.set_defaults(func=_cmd_diff)

    args = parser.parse_args()
    handler: _CmdHandler = args.func
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
