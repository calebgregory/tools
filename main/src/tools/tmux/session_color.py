"""Store each tmux session's name color on the session as user options.

The session list in the status bar colors every name the way a window title would
color a directory of that name (see `window_status`). tmux cannot do that inline:
a `#(...)` command inside a `#{S:...}` loop runs once, not once per session, so
the color has to be computed ahead of time and read back as a plain option.
This writes `@name_color_dark` and `@name_color_light` on the session; the
status formats in `.tmux.conf` pick one by `@appearance`.

Run with session ids to color those sessions, or with no arguments to color
every session on the server. Meant to be run from the `session-created` and
`session-renamed` hooks and once when the config loads.
"""

import subprocess
import sys
import typing as ty

from tools.tmux.window_status import name_color


class SessionColors(ty.NamedTuple):
    dark: str
    light: str


def session_colors(name: str) -> SessionColors:
    return SessionColors(dark=name_color(name, "dark"), light=name_color(name, "light"))


def _tmux(*args: str) -> str:
    return subprocess.run(["tmux", *args], check=True, capture_output=True, text=True).stdout


def _all_session_ids() -> list[str]:
    return _tmux("list-sessions", "-F", "#{session_id}").split()


def _session_name(session_id: str) -> str:
    return _tmux("display-message", "-p", "-t", session_id, "#{session_name}").rstrip("\n")


def _store(session_id: str, colors: SessionColors) -> None:
    _tmux("set-option", "-t", session_id, "@name_color_dark", colors.dark)
    _tmux("set-option", "-t", session_id, "@name_color_light", colors.light)


def main(argv: ty.Sequence[str] = sys.argv[1:]) -> None:
    session_ids = list(argv) or _all_session_ids()
    for session_id in session_ids:
        _store(session_id, session_colors(_session_name(session_id)))


if __name__ == "__main__":
    main()
