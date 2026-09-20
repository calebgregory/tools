from datetime import datetime, timezone

import pytest

from tools.gmail import client


def _summary(
    *,
    message_id: str = "m1",
    sender: str = "sender@example.com",
    subject: str = "a subject",
    received: datetime = datetime(2026, 1, 1, tzinfo=timezone.utc),
) -> client.MessageSummary:
    return client.MessageSummary(id=message_id, sender=sender, subject=subject, received=received)


def _raw_message(
    *,
    message_id: str = "m1",
    from_header: str = "Sender <sender@example.com>",
    subject: str = "a subject",
    internal_date_ms: int = 1767225600000,  # 2026-01-01T00:00:00Z
) -> dict:
    return {
        "id": message_id,
        "internalDate": str(internal_date_ms),
        "payload": {
            "headers": [
                {"name": "From", "value": from_header},
                {"name": "Subject", "value": subject},
            ]
        },
    }


@pytest.mark.parametrize(
    "from_header,expected",
    [
        ('"Foo Bar" <Foo@Bar.com>', "foo@bar.com"),
        ("foo@bar.com", "foo@bar.com"),
        ("Foo Bar <foo+tag@bar.com>", "foo+tag@bar.com"),
        ("  MAILER-DAEMON  ", "mailer-daemon"),
    ],
)
def test_address_of_normalizes_the_from_header(from_header: str, expected: str) -> None:
    assert client._address_of(from_header) == expected


def test_xf_message_to_summary() -> None:
    raw = _raw_message(message_id="abc", from_header="Newsletter <news@example.com>", subject="Hi")

    assert client._xf_message_to_summary(raw) == client.MessageSummary(
        id="abc",
        sender="news@example.com",
        subject="Hi",
        received=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def test_xf_message_to_summary_tolerates_a_missing_subject() -> None:
    raw = _raw_message()
    raw["payload"]["headers"] = [{"name": "From", "value": "sender@example.com"}]

    assert client._xf_message_to_summary(raw).subject == ""


def test_tally_by_sender_counts_and_dates_each_sender() -> None:
    messages = [
        _summary(sender="a@x.com", received=datetime(2026, 1, 1, tzinfo=timezone.utc)),
        _summary(sender="a@x.com", subject="newest", received=datetime(2026, 3, 1, tzinfo=timezone.utc)),
        _summary(sender="b@y.com", received=datetime(2026, 2, 1, tzinfo=timezone.utc)),
    ]

    assert client.tally_by_sender(messages) == [
        client.SenderTally(
            sender="a@x.com",
            message_count=2,
            oldest=datetime(2026, 1, 1, tzinfo=timezone.utc),
            newest=datetime(2026, 3, 1, tzinfo=timezone.utc),
            sample_subjects=("newest",),
        ),
        client.SenderTally(
            sender="b@y.com",
            message_count=1,
            oldest=datetime(2026, 2, 1, tzinfo=timezone.utc),
            newest=datetime(2026, 2, 1, tzinfo=timezone.utc),
            sample_subjects=("a subject",),
        ),
    ]


def test_tally_by_sender_breaks_count_ties_alphabetically() -> None:
    messages = [_summary(sender="b@y.com"), _summary(sender="a@x.com")]

    assert [tally.sender for tally in client.tally_by_sender(messages)] == ["a@x.com", "b@y.com"]


def test_chunks_splits_on_the_size_boundary() -> None:
    assert list(client._chunks(["a", "b", "c", "d", "e"], 2)) == [["a", "b"], ["c", "d"], ["e"]]


def test_chunks_of_an_empty_sequence_yields_nothing() -> None:
    assert list(client._chunks([], 10)) == []
