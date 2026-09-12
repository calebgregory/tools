"""Colored tmux window titles.

A shell window reads `$parent/child`, each segment colored by a hash of its own name
so sibling directories share a prefix color. A window running a program reads
`program: parent/child`, or just `program` for editors and agents whose launch
directory is not what you need to see.

Argv contract (positional, in this order): pane_path, pane_current_path,
pane_current_command, pane_title. `pane_path` comes from OSC 7 and wins when set;
`pane_current_path` is the process cwd fallback. Output is a tmux format string
using `#[fg=...]` directives, so it must be spliced in via `#(...)`.
"""

import os
import re
import sys
import typing as ty

_PALETTE = [
    "#FF5555",  # bright red
    "#50FA7B",  # bright green
    "#F1FA8C",  # bright yellow
    "#A66BE0",  # bright purple
    "#FF79C6",  # bright pink
    "#8BE9FD",  # bright cyan
    "#FFB86C",  # bright orange
    "#9AEDFE",  # light blue
    "#5AF78E",  # light green
    "#F4F99D",  # light yellow
    "#CAA9FA",  # light purple
    "#FF6E67",  # light red
    "#ADEDC8",  # soft green
    "#FEA44D",  # soft orange
    "#F07178",  # coral
    "#00B1B3",  # teal
    "#E6DB74",  # muted yellow
    "#7DCFFF",  # sky blue
    "#D8A0DF",  # lavender
    "#36C2C2",  # aqua
    "#FF9E64",  # peach
    "#85DACC",  # mint
    "#E3CF65",  # gold
]

_DIR_COLORS = {
    "apps": "#00FFFF",
    "libs": "#F1FA8C",
    "mops": "#50FA7B",
}

_PROCESS_COLORS = {
    "claude": "#50FA7B",
    "codex": "#26A34A",
    "opencode": "#7DCFFF",
    "emacs": "#FFB86C",
    "emacsclient": "#E0922D",
    "git": "#BB55FF",
    "python": "#F1FA8C",
    "python3": "#F1FA8C",
    "node": "#50FA7B",
    "npm": "#50FA7B",
}

# Shown as `$dir`: the shell itself is not news.
_SHELLS = {"xonsh", "bash", "zsh", "fish", "sh", "starship", "mise"}

# Shown by name only: where these were launched from is not what you look for.
_STANDALONE = {
    "claude",
    "codex",
    "opencode",
    "emacs",
    "emacsclient",
    "lma",
    "vim",
    "nvim",
    "htop",
    "top",
}

# Claude Code reports its version string as its process name.
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
# Interpreters whose name says nothing about what they run; the pane title usually does.
_INTERPRETER_RE = re.compile(r"^(?:python|node|ruby|perl)\d*(?:\.\d+)?$")
# A python with no informative title is an interactive shell (xonsh, ipython).
_PYTHON_RE = re.compile(r"^python\d*(?:\.\d+)?$")
_TITLE_SHELL_NAMES = {"bash", "zsh", "fish", "xonsh", "-bash", "-zsh", "sh"}


def _djb2(s: str) -> int:
    h = 5381
    for c in s:
        h = ((h * 33) + ord(c)) & 0xFFFFFFFF
    return h


def _dir_color(name: str) -> str:
    return _DIR_COLORS.get(name, _PALETTE[_djb2(name) % len(_PALETTE)])


def _process_color(name: str) -> str:
    return _PROCESS_COLORS.get(name, _PALETTE[_djb2(name) % len(_PALETTE)])


def _colored(text: str, color: str) -> str:
    return f"#[fg={color}]{text}#[fg=default]"


def _normalize_path(path: str) -> str:
    """Strip an OSC 7 `file://host` prefix and fold $HOME to `~`."""
    if path.startswith("file://"):
        without_scheme = path[len("file://") :]
        slash = without_scheme.find("/")
        path = without_scheme[slash:] if slash != -1 else ""
    home = os.environ.get("HOME", "")
    if home and (path == home or path.startswith(home + "/")):
        path = "~" + path[len(home) :]
    return path


def _display_segments(path: str) -> list[str]:
    path = _normalize_path(path)
    parts = [p for p in path.split("/") if p]
    if not parts:
        return ["/"]
    is_root_level = len(parts) == 1 and path.startswith("/")
    return ["/" + parts[0]] if is_root_level else parts[-2:]


def format_path(path: str) -> str:
    return "/".join(_colored(seg, _dir_color(seg)) for seg in _display_segments(path))


def _app_from_title(title: str | None, path: str) -> str | None:
    """First word of the pane title, unless it is a path, a host, a shell, or the cwd name."""
    words = (title or "").split()
    if not words:
        return None
    first = words[0]
    if first.startswith(("/", "~")) or "@" in first or first in _TITLE_SHELL_NAMES:
        return None
    basename = _normalize_path(path).rstrip("/").rsplit("/", 1)[-1]
    if first == basename:
        return None
    return first


def _resolve_program(process: str | None, title: str | None, path: str) -> str | None:
    """Name of the program worth showing, or None when the window is just a shell."""
    if not process or process in _SHELLS:
        return None
    if _VERSION_RE.match(process):
        return "claude"
    if _INTERPRETER_RE.match(process):
        from_title = _app_from_title(title, path)
        if from_title:
            return from_title
        return None if _PYTHON_RE.match(process) else process
    return process


def format_window(path: str, process: str | None = None, title: str | None = None) -> str:
    program = _resolve_program(process, title, path)
    if program is None:
        return "$" + format_path(path)
    colored_program = _colored(program, _process_color(program))
    if program in _STANDALONE:
        return colored_program
    return f"{colored_program}: {format_path(path)}"


def main(argv: ty.Sequence[str] = sys.argv[1:]) -> None:
    if len(argv) < 2:
        print(
            "usage: tmux-window-status <pane_path> <pane_current_path> [command] [title]",
            file=sys.stderr,
        )
        sys.exit(2)
    pane_path, pane_current_path = argv[0], argv[1]
    process = argv[2] if len(argv) > 2 else None
    title = argv[3] if len(argv) > 3 else None
    print(format_window(pane_path or pane_current_path, process, title))


if __name__ == "__main__":
    main()
