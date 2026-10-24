from tools.tmux import window_status
from tools.tmux.session_labels import SessionLabel, session_labels


def test_session_labels_number_and_color_sessions_by_position() -> None:
    result = session_labels(["$4", "$0"])

    assert result == [
        SessionLabel("$4", 0, window_status.palette_color(0, "dark"), window_status.palette_color(0, "light")),
        SessionLabel("$0", 1, window_status.palette_color(1, "dark"), window_status.palette_color(1, "light")),
    ]


def test_session_labels_wrap_around_the_palette() -> None:
    palette_size = len(window_status._PALETTES["dark"].ordered)
    session_ids = [f"${n}" for n in range(palette_size + 1)]

    result = session_labels(session_ids)

    assert result[palette_size].color_dark == result[0].color_dark
    assert result[palette_size].index == palette_size


def test_session_labels_with_no_sessions() -> None:
    assert session_labels([]) == []
