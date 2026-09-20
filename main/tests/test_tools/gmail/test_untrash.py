from tools.gmail import untrash


def test_parse_audit_log_skips_the_header_comment() -> None:
    text = "# gmail-trash-sender 2026-09-19T22:15:00+00:00\na@x.com\tm1\na@x.com\tm2\nb@y.com\tm3\n"

    assert untrash.parse_audit_log(text) == [
        untrash.LoggedMessage(sender="a@x.com", id="m1"),
        untrash.LoggedMessage(sender="a@x.com", id="m2"),
        untrash.LoggedMessage(sender="b@y.com", id="m3"),
    ]


def test_parse_audit_log_ignores_lines_with_no_message_id() -> None:
    text = "# header\n\na@x.com\nb@y.com\tm1\n"

    assert untrash.parse_audit_log(text) == [untrash.LoggedMessage(sender="b@y.com", id="m1")]
