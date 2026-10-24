"""Give every tmux session a number and a color, stored on the session as options.

The status bar shows sessions as `0: notes`, `1: edi-kat`, ... and `prefix+<digit>`
switches to the session with that number. The color is dealt round robin from the
window-title palette in `colors.json`: position n takes palette entry n, so the
number and the color always travel together and no two sessions share a color
until the palette runs out.

tmux cannot do either inline. Its format language has no loop counter, and a
`#(...)` inside a `#{S:...}` loop runs once, not once per session. So this writes
`@index`, `@session_color_dark` and `@session_color_light` on each session and
the formats in `.tmux.conf` read them back.

Position is creation order, because that is the order a `#{S:...}` loop renders
(`list-sessions` sorts by name unless told otherwise). A new session takes the
next number; closing one shifts the numbers, and with them the colors, of the
sessions after it. The `session-created`, `session-renamed` and `session-closed`
hooks in `.tmux.conf` run this with no arguments.
"""

import subprocess
import sys
import typing as ty

from tools.tmux.window_status import palette_color


class SessionLabel(ty.NamedTuple):
    session_id: str
    index_: int  # .index is already a method on tuple
    color_dark: str
    color_light: str


def session_labels(session_ids_in_creation_order: ty.Sequence[str]) -> list[SessionLabel]:
    return [
        SessionLabel(
            session_id=session_id,
            index_=index,
            color_dark=palette_color(index, "dark"),
            color_light=palette_color(index, "light"),
        )
        for index, session_id in enumerate(session_ids_in_creation_order)
    ]


def _tmux(*args: str) -> str:
    return subprocess.run(["tmux", *args], check=True, capture_output=True, text=True).stdout


def _session_ids_in_creation_order() -> list[str]:
    return _tmux("list-sessions", "-O", "creation", "-F", "#{session_id}").split()


def _store(label: SessionLabel) -> None:
    _tmux("set-option", "-t", label.session_id, "@index", str(label.index_))
    _tmux("set-option", "-t", label.session_id, "@session_color_dark", label.color_dark)
    _tmux("set-option", "-t", label.session_id, "@session_color_light", label.color_light)


def main(argv: ty.Sequence[str] = sys.argv[1:]) -> None:
    for label in session_labels(_session_ids_in_creation_order()):
        _store(label)


if __name__ == "__main__":
    main()
