#!/usr/bin/env python3
"""Move every message from one or more senders to Trash.

Trash rather than delete: Gmail keeps trashed messages for 30 days, so a sender match
that turns out to be too broad stays recoverable. These tools never request the scope
that permanent deletion needs.

Before trashing anything, a run writes every message id it is about to touch to
`.out/logs/`, and `gmail-untrash` replays that file to put them back.

    gmail-trash-sender --sender newsletter@example.com
    gmail-trash-sender --sender a@example.com --sender b@example.com --query older_than:6m
    gmail-trash-sender --sender newsletter@example.com --yes
"""

import argparse
import logging
import typing as ty
from datetime import datetime, timezone
from pathlib import Path

from thds.core.project_root import find_project_root
from thds.termtool.colorize import colorized

from tools.gmail import client

logger = logging.getLogger(__name__)

_BLUE = colorized(fg="blue")
_YELLOW = colorized(fg="yellow")

_LOGS_DIR = find_project_root(Path(__file__)) / ".out/logs"
_PREVIEW_MESSAGES = 3


class SenderPlan(ty.NamedTuple):
    sender: str
    query: str
    ids: tuple[str, ...]
    preview: tuple[client.MessageSummary, ...]


def _query_for(sender: str, extra: str) -> str:
    return f"from:{sender} {extra}".strip()


def _plan(service: client.Service, sender: str, extra_query: str) -> SenderPlan:
    query = _query_for(sender, extra_query)
    ids = client.message_ids(service, query)
    return SenderPlan(
        sender=sender,
        query=query,
        ids=tuple(ids),
        preview=tuple(client.summaries(service, ids[:_PREVIEW_MESSAGES])),
    )


def _plan_lines(plan: SenderPlan) -> list[str]:
    if not plan.ids:
        return [f"{plan.sender}: {_YELLOW('no matches')} for {plan.query!r}"]
    return [
        f"{plan.sender}: {len(plan.ids)} messages",
        *(
            f"    {message.received:%Y-%m-%d}  {message.subject[:60]}"
            for message in sorted(plan.preview, key=lambda m: m.received, reverse=True)
        ),
    ]


def _render_plans(plans: ty.Sequence[SenderPlan]) -> str:
    return "\n".join(
        [
            *(line for plan in plans for line in _plan_lines(plan)),
            "",
            f"{sum(len(plan.ids) for plan in plans)} messages would move to Trash "
            "(recoverable for 30 days)",
        ]
    )


def _write_audit_log(plans: ty.Sequence[SenderPlan], *, now: datetime) -> Path:
    log_file = _LOGS_DIR / f"gmail-trash-{now:%Y%m%dT%H%M%S}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(
        "\n".join(
            [
                f"# gmail-trash-sender {now.isoformat(timespec='seconds')}",
                *(f"{plan.sender}\t{message_id}" for plan in plans for message_id in plan.ids),
            ]
        )
        + "\n"
    )
    return log_file


def main(*, senders: ty.Sequence[str], extra_query: str, assume_yes: bool) -> None:
    service = client.service()
    plans = [_plan(service, sender, extra_query) for sender in senders]
    if not any(plan.ids for plan in plans):
        print("nothing matched; leaving the mailbox alone")
        return

    print(_render_plans(plans))

    if not assume_yes and input(_BLUE("Move these to Trash? [y/N] ")).strip().lower() != "y":
        print("skipped")
        return

    log_file = _write_audit_log(plans, now=datetime.now(tz=timezone.utc))
    logger.warning("recorded %s before trashing; undo with gmail-untrash %s", log_file, log_file)

    trashed = sum(client.trash(service, plan.ids) for plan in plans if plan.ids)
    print(f"trashed {trashed} messages; undo with: gmail-untrash {log_file}")


def cli() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--sender", action="append", required=True, help="sender address; repeatable")
    parser.add_argument(
        "--query", default="", help="extra Gmail query terms, e.g. 'older_than:6m is:unread'"
    )
    parser.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    main(senders=args.sender, extra_query=args.query, assume_yes=args.yes)


if __name__ == "__main__":
    cli()
