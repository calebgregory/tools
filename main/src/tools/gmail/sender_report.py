#!/usr/bin/env python3
"""Rank the senders filling a mailbox, so a human or an agent can decide which ones are
worth bulk-trashing.

Read-only. Nothing here modifies the mailbox; feed the senders it names to
`gmail-trash-sender` once the decision is made.

Scanning costs one metadata fetch per message, so `--limit` bounds how long a run takes.
The default scans the most recent 2000 matches, which is enough to see who the repeat
offenders are.

    gmail-sender-report
    gmail-sender-report --query "in:inbox older_than:1y" --limit 5000 --top 40
    gmail-sender-report --format json
"""

import argparse
import json
import logging
import typing as ty

from tools.gmail import client

_DEFAULT_QUERY = "in:inbox is:unread"

Format = ty.Literal["table", "json"]

_SENDER_WIDTH = 44
_SUBJECT_WIDTH = 48


def _render_table(tallies: ty.Sequence[client.SenderTally], *, top: int, scanned: int, query: str) -> str:
    shown = tallies[:top]
    rows = [
        f"{tally.message_count:>6}  {tally.sender[:_SENDER_WIDTH]:<{_SENDER_WIDTH}}  "
        f"{tally.oldest:%Y-%m-%d}..{tally.newest:%Y-%m-%d}  "
        f"{(tally.sample_subjects[0] if tally.sample_subjects else '')[:_SUBJECT_WIDTH]}"
        for tally in shown
    ]
    return "\n".join(
        [
            f"query    {query}",
            f"scanned  {scanned} messages from {len(tallies)} senders (showing the top {len(shown)})",
            "",
            f"{'count':>6}  {'sender':<{_SENDER_WIDTH}}  {'received':<21}  most recent subject",
            *rows,
        ]
    )


def _render_json(tallies: ty.Sequence[client.SenderTally], *, top: int) -> str:
    return json.dumps([tally._asdict() for tally in tallies[:top]], default=str, indent=2)


def _render(
    tallies: ty.Sequence[client.SenderTally],
    *,
    output_format: Format,
    top: int,
    scanned: int,
    query: str,
) -> str:
    if output_format == "json":
        return _render_json(tallies, top=top)
    return _render_table(tallies, top=top, scanned=scanned, query=query)


def scan_and_report(query: str, limit: int, top: int, format: Format) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    service = client.service()
    ids = client.message_ids(service, query, limit=limit)
    if not ids:
        print(f"no messages match {query!r}")
        return

    messages = client.summaries(service, ids)
    print(
        _render(
            client.tally_by_sender(messages),
            output_format=format,
            top=top,
            scanned=len(messages),
            query=query,
        )
    )


def cli() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--query", default=_DEFAULT_QUERY, help="Gmail search query to scan")
    parser.add_argument("--limit", type=int, default=2000, help="stop after this many matching messages")
    parser.add_argument("--top", type=int, default=25, help="how many senders to report")
    parser.add_argument("--format", choices=ty.get_args(Format), default="table")
    args = parser.parse_args()

    scan_and_report(args.query, args.limit, args.top, args.format)


if __name__ == "__main__":
    cli()
