#!/usr/bin/env python3
"""Restore the messages named in a `gmail-trash-sender` audit log.

Gmail purges Trash after 30 days, so this only works while the messages are still there.

    gmail-untrash .out/logs/gmail-trash-20260919T221500.log
    gmail-untrash .out/logs/gmail-trash-20260919T221500.log --sender newsletter@example.com
"""

import argparse
import logging
import typing as ty
from pathlib import Path

from thds.termtool.colorize import colorized

from tools.gmail import client

logger = logging.getLogger(__name__)

_BLUE = colorized(fg="blue")


class LoggedMessage(ty.NamedTuple):
    sender: str
    id: str


def parse_audit_log(text: str) -> list[LoggedMessage]:
    return [
        LoggedMessage(sender=sender, id=message_id)
        for line in text.splitlines()
        if line and not line.startswith("#")
        for sender, _, message_id in [line.partition("\t")]
        if message_id
    ]


def main(*, log_file: Path, senders: ty.Sequence[str], assume_yes: bool) -> None:
    logged = parse_audit_log(log_file.read_text())
    if senders:
        logged = [message for message in logged if message.sender in senders]
    if not logged:
        print(f"no message ids in {log_file}")
        return

    by_sender = sorted({message.sender for message in logged})
    print(f"{len(logged)} messages from {len(by_sender)} senders: {', '.join(by_sender)}")

    if not assume_yes and input(_BLUE("Restore these from Trash? [y/N] ")).strip().lower() != "y":
        print("skipped")
        return

    restored = client.untrash(client.service(), [message.id for message in logged])
    print(f"restored {restored} messages")


def cli() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("log_file", type=Path, help="audit log written by gmail-trash-sender")
    parser.add_argument(
        "--sender", action="append", default=[], help="restore only this sender; repeatable"
    )
    parser.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    main(log_file=args.log_file, senders=args.sender, assume_yes=args.yes)


if __name__ == "__main__":
    cli()
