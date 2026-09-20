"""Search, summarize and trash messages over the Gmail REST API.

Queries are Gmail's own search syntax (`from:`, `older_than:`, `is:unread`), so a caller
passes whatever it would type into the Gmail search box.
"""

import collections
import email.utils
import functools
import logging
import time
import typing as ty
from datetime import datetime, timezone

from googleapiclient.discovery import build

from tools.gmail import auth

logger = logging.getLogger(__name__)

_USER = "me"
_LIST_PAGE_SIZE = 500
_METADATA_BATCH_SIZE = 100
_MODIFY_BATCH_SIZE = 1000  # batchModify's documented ceiling

# A metadata get costs 5 quota units against a 250-unit-per-second per-user ceiling, so a
# 100-message batch needs about two seconds of spacing to stay under it.
_BATCH_PAUSE_SECONDS = 2.0

_TRASH_LABEL = "TRASH"

Service = ty.Any  # googleapiclient builds its resources dynamically; there is no real type


class MessageSummary(ty.NamedTuple):
    id: str
    sender: str
    subject: str
    received: datetime


class SenderTally(ty.NamedTuple):
    sender: str
    message_count: int  # not `count`, which a NamedTuple inherits from tuple
    oldest: datetime
    newest: datetime
    sample_subjects: tuple[str, ...]


def service() -> Service:
    return build("gmail", "v1", credentials=auth.credentials(), cache_discovery=False)


def _address_of(from_header: str) -> str:
    """`"Foo Bar" <Foo@Bar.com>` becomes `foo@bar.com`; an unparseable header comes back whole."""
    _, address = email.utils.parseaddr(from_header)
    return address.lower() or from_header.strip().lower()


def _header(message: dict[str, ty.Any], name: str) -> str:
    for header in message.get("payload", {}).get("headers", []):
        if header.get("name", "").lower() == name.lower():
            return str(header.get("value", ""))
    return ""


def _xf_message_to_summary(message: dict[str, ty.Any]) -> MessageSummary:
    return MessageSummary(
        id=message["id"],
        sender=_address_of(_header(message, "From")),
        subject=_header(message, "Subject"),
        received=datetime.fromtimestamp(int(message["internalDate"]) / 1000, tz=timezone.utc),
    )


def _chunks(items: ty.Sequence[str], size: int) -> ty.Iterator[ty.Sequence[str]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def message_ids(service: Service, query: str, *, limit: int | None = None) -> list[str]:
    ids: list[str] = []
    request = service.users().messages().list(userId=_USER, q=query, maxResults=_LIST_PAGE_SIZE)
    while request is not None:
        response = request.execute()
        ids.extend(message["id"] for message in response.get("messages", []))
        if limit is not None and len(ids) >= limit:
            return ids[:limit]
        request = service.users().messages().list_next(request, response)
    return ids


def _collect(
    collected: list[MessageSummary],
    request_id: str,
    response: dict[str, ty.Any] | None,
    exception: Exception | None,
) -> None:
    if exception is not None:
        logger.warning("metadata fetch failed (request %s): %s", request_id, exception)
        return
    assert response is not None
    collected.append(_xf_message_to_summary(response))


def summaries(service: Service, ids: ty.Sequence[str]) -> list[MessageSummary]:
    collected: list[MessageSummary] = []
    for batch_number, chunk in enumerate(_chunks(ids, _METADATA_BATCH_SIZE)):
        if batch_number:
            time.sleep(_BATCH_PAUSE_SECONDS)
        batch = service.new_batch_http_request(callback=functools.partial(_collect, collected))
        for message_id in chunk:
            batch.add(
                service.users()
                .messages()
                .get(
                    userId=_USER,
                    id=message_id,
                    format="metadata",
                    metadataHeaders=["From", "Subject"],
                )
            )
        batch.execute()
        logger.info("fetched metadata for %d of %d messages", len(collected), len(ids))
    return collected


def tally_by_sender(
    messages: ty.Iterable[MessageSummary], *, samples: int = 1
) -> list[SenderTally]:
    by_sender: dict[str, list[MessageSummary]] = collections.defaultdict(list)
    for message in messages:
        by_sender[message.sender].append(message)

    tallies = [
        SenderTally(
            sender=sender,
            message_count=len(group),
            oldest=min(message.received for message in group),
            newest=max(message.received for message in group),
            sample_subjects=tuple(
                message.subject
                for message in sorted(group, key=lambda m: m.received, reverse=True)[:samples]
            ),
        )
        for sender, group in by_sender.items()
    ]
    return sorted(tallies, key=lambda tally: (-tally.message_count, tally.sender))


def trash(service: Service, ids: ty.Sequence[str]) -> int:
    trashed = 0
    for chunk in _chunks(ids, _MODIFY_BATCH_SIZE):
        logger.warning("trashing %d messages, first id %s", len(chunk), chunk[0])
        service.users().messages().batchModify(
            userId=_USER, body={"ids": list(chunk), "addLabelIds": [_TRASH_LABEL]}
        ).execute()
        trashed += len(chunk)
    return trashed


def untrash(service: Service, ids: ty.Sequence[str]) -> int:
    restored = 0
    for chunk in _chunks(ids, _MODIFY_BATCH_SIZE):
        logger.warning("restoring %d messages from trash, first id %s", len(chunk), chunk[0])
        service.users().messages().batchModify(
            userId=_USER, body={"ids": list(chunk), "removeLabelIds": [_TRASH_LABEL]}
        ).execute()
        restored += len(chunk)
    return restored
