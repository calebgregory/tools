"""Number every tmux session by its position in the session list.

The status bar shows sessions as `0: notes`, `1: edi-kat`, ... and `prefix+<digit>`
switches to the session with that number. tmux has no loop counter in its
format language, so the position is written to each session as the `@index`
user option. The order is creation order, because that is the order a
`#{S:...}` loop renders and `list-sessions` sorts by name unless told otherwise.
A new session therefore takes the next free number instead of renumbering the
ones before it. Positions still shift
whenever a session appears, disappears or is renamed, so this always renumbers
every session; the `session-created`, `session-renamed` and `session-closed`
hooks in `.tmux.conf` run it.
"""

import subprocess
import sys
import typing as ty


class IndexAssignment(ty.NamedTuple):
    session_id: str
    idx: int


def index_assignments(session_ids: ty.Sequence[str]) -> list[IndexAssignment]:
    return [IndexAssignment(session_id, idx) for idx, session_id in enumerate(session_ids)]


def _tmux(*args: str) -> str:
    return subprocess.run(["tmux", *args], check=True, capture_output=True, text=True).stdout


def _all_session_ids() -> list[str]:
    return _tmux("list-sessions", "-O", "creation", "-F", "#{session_id}").split()


def main(argv: ty.Sequence[str] = sys.argv[1:]) -> None:
    for assignment in index_assignments(_all_session_ids()):
        _tmux("set-option", "-t", assignment.session_id, "@index", str(assignment.idx))


if __name__ == "__main__":
    main()
