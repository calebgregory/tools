"""Give every tmux session a number and a color, stored on the session as options.

The status bar's session row reads `0: notes  1: edi-kat  ...` and prefix+j/k walk
that order. The number is the session's `@index` option and nothing else. tmux has no
reorderable session list (ids and creation times are fixed), so the order lives in
that option: a new session takes the next number, closing one compacts the numbers
after it, and `move` puts a session at a position of your choosing and shifts the
others. The color is dealt round robin from the window-title palette in
`colors.json`: position n takes palette entry n, so the number and the color always
travel together and no two sessions share a color until the palette runs out.

tmux cannot render the row inline. A `#{S:...}` loop walks sessions in creation
order with no way to sort it, and the format language has no loop counter. So every
run writes, per session, `@index`, `@session_color_dark`, `@session_color_light`,
`@next_session` and `@prev_session` (ids, wrapping at the ends), and globally
`@session_row`, the whole row as a format string for `status-format` to expand with
`#{E:...}`. Run with no arguments (`sync`) after any session is created, renamed or
closed.

`choose-tree` has the same limitation (it sorts sessions only by id, name or activity),
so `menu` opens a `display-menu` session picker in the same order instead.
"""

import argparse
import subprocess
import sys
import typing as ty

from tools.tmux.window_status import chrome_color, palette_color, parse_appearance


class Session(ty.NamedTuple):
    session_id: str
    name: str
    index_: int | None  # None until this module first labels it; .index is a tuple method


class SessionLabel(ty.NamedTuple):
    session_id: str
    name: str
    index_: int
    color_dark: str
    color_light: str


def _is_hidden_session(session: Session) -> bool:
    """Tools keep their hidden sessions under names starting with `_` (lemonaid's popup
    residents are `_lma_*`, with `status off`). Walking a client into one hides the status
    bar and can trip the tool's own hooks, so we give them no label and hide them from the
    status bar."""
    return session.name.startswith("_")


def session_order(sessions_in_creation_order: ty.Sequence[Session]) -> list[Session]:
    """Labelled sessions in `@index` order, then the unlabelled ones in creation order,
    leaving out hidden sessions."""
    return sorted(
        (session for session in sessions_in_creation_order if not _is_hidden_session(session)),
        key=lambda session: (1, 0) if session.index_ is None else (0, session.index_),
    )


def moved(sessions: ty.Sequence[Session], session_id: str, position: int) -> list[Session]:
    """`sessions` with `session_id` at `position`, clamped to the ends, the rest shifted."""
    moving = [session for session in sessions if session.session_id == session_id]
    if not moving:
        raise ValueError(f"no session {session_id}")
    others = [session for session in sessions if session.session_id != session_id]
    clamped = max(0, min(position, len(others)))
    return [*others[:clamped], *moving, *others[clamped:]]


def session_labels(sessions_in_order: ty.Sequence[Session]) -> list[SessionLabel]:
    return [
        SessionLabel(
            session_id=session.session_id,
            name=session.name,
            index_=index,
            color_dark=palette_color(index, "dark"),
            color_light=palette_color(index, "light"),
        )
        for index, session in enumerate(sessions_in_order)
    ]


def session_row(labels: ty.Sequence[SessionLabel]) -> str:
    """The session row as a tmux format: `<index>: <name>` per session with the name in
    its color, and the expanding client's own session bold and underlined. Each entry
    sits in a range=session marker so a mouse click switches to it.

    The format expands in the client's session and cannot reach another session's
    options, so each entry carries both colors and picks one on `@appearance`."""
    return "#[align=left]" + "".join(_row_entry(label) for label in labels)


def _literal(text: str) -> str:
    """`#` starts an alias in a format (`#F` is the window flags), so a literal one is `##`."""
    return text.replace("#", "##")


def _color(label: SessionLabel) -> str:
    return (
        f"#{{?#{{==:#{{@appearance}},light}},{_literal(label.color_light)},{_literal(label.color_dark)}}}"
    )


def _is_current(label: SessionLabel) -> str:
    return f"#{{==:#{{session_id}},{label.session_id}}}"


def _row_entry(label: SessionLabel) -> str:
    color = _color(label)
    is_current = _is_current(label)
    name = _literal(label.name)
    return (
        f"#[range=session|{label.session_id}]"
        f"#{{?{is_current},#[bold#,underscore#,us={color}],}}"
        f" {label.index_}: #[fg={color}]{name}#[fg=default] "
        "#[norange default] "
    )


def session_menu_items(labels: ty.Sequence[SessionLabel]) -> list[str]:
    """`display-menu` item arguments (name, key, command per session) in `labels` order.

    tmux expands each name as a format in the client's session, so the colors and the
    bold current session work as in `session_row`. Only sessions 0-9 get a shortcut key,
    so that the key is always the number the session row shows."""
    return [
        arg
        for label in labels
        for arg in (
            f"#{{?{_is_current(label)},#[bold],}}{label.index_}: #[fg={_color(label)}]{_literal(label.name)}",
            str(label.index_) if label.index_ < 10 else "",
            f"switch-client -t '{label.session_id}'",
        )
    ]


def _tmux(*args: str) -> str:
    return subprocess.run(["tmux", *args], check=True, capture_output=True, text=True).stdout


def _sessions_in_creation_order() -> list[Session]:
    listing = _tmux("list-sessions", "-O", "creation", "-F", "#{session_id}\t#{session_name}\t#{@index}")
    return [
        Session(session_id, name, int(index) if index else None)
        for session_id, name, index in (line.split("\t") for line in listing.splitlines())
    ]


def _store(labels: ty.Sequence[SessionLabel]) -> None:
    """One tmux call with every option write, `;`-separated, so the row never shows a
    half-written state."""
    per_session = [
        arg
        for position, label in enumerate(labels)
        for arg in (
            *("set-option", "-t", label.session_id, "@index", str(label.index_), ";"),
            *("set-option", "-t", label.session_id, "@session_color_dark", label.color_dark, ";"),
            *("set-option", "-t", label.session_id, "@session_color_light", label.color_light, ";"),
            *(
                "set-option",
                "-t",
                label.session_id,
                "@next_session",
                labels[(position + 1) % len(labels)].session_id,
                ";",
            ),
            *("set-option", "-t", label.session_id, "@prev_session", labels[position - 1].session_id, ";"),
        )
    ]
    _tmux(*per_session, "set-option", "-g", "@session_row", session_row(labels))


def main(argv: ty.Sequence[str] = sys.argv[1:]) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("sync", help="keep the order, number new sessions, close gaps (the default)")
    move = commands.add_parser("move", help="put a session at a position, shifting the others")
    move.add_argument("session_id", help="$-prefixed id, as #{session_id} gives it")
    move.add_argument("position", type=int)
    menu = commands.add_parser("menu", help="pick a session from a menu in the session row's order")
    menu.add_argument("client", help="the client to show the menu on, as #{client_name} gives it")
    menu.add_argument("appearance", nargs="?", help="light or dark, as #{@appearance} gives it")
    args = parser.parse_args(argv)

    sessions = session_order(_sessions_in_creation_order())
    if args.command == "menu":
        # A menu ignores attributes like reverse in its selected style and takes only the
        # colors, so a per-session highlight is not possible; use the current window's gray.
        selected_bg = chrome_color("current_bg", parse_appearance(args.appearance))
        _tmux(
            *(
                "display-menu",
                "-c",
                args.client,
                "-T",
                "sessions",
                "-x",
                "C",
                "-y",
                "C",
                "-H",
                f"bg={selected_bg}",
            ),
            *session_menu_items(session_labels(sessions)),
        )
        return
    if args.command == "move":
        sessions = moved(sessions, args.session_id, args.position)
    _store(session_labels(sessions))


if __name__ == "__main__":
    main()
