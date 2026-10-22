from tools.tmux import window_status
from tools.tmux.session_color import SessionColors, session_colors


def test_session_colors_match_window_title_colors() -> None:
    result = session_colors("edi-kat")

    assert result == SessionColors(
        dark=window_status.name_color("edi-kat", "dark"),
        light=window_status.name_color("edi-kat", "light"),
    )


def test_session_colors_follow_dir_color_overrides() -> None:
    result = session_colors("apps")

    assert result == SessionColors(
        dark=window_status._PALETTES["dark"].dirs["apps"],
        light=window_status._PALETTES["light"].dirs["apps"],
    )
