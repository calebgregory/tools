"""Colored tmux window titles.

A shell window reads `$par/child`, where the parent is shortened to its first three
characters, or to an alias from `_DIR_ALIASES` for the directories you live in. Each
segment takes its color from a hash of its full name, so sibling directories share a
prefix color and shortening a name does not recolor it. A window running a program
reads `program: par/child`, or just `program` for editors and agents whose launch
directory is not what you need to see.

Colors come from `colors.json` beside this module, which `dotfiles/.wezterm.lua`
also reads so wezterm tab titles color the same names the same way. Only the djb2
hash itself is written twice, once per language.

Argv contract (positional, in this order): pane_path, pane_current_path,
pane_current_command, pane_title. `pane_path` comes from OSC 7 and wins when set;
`pane_current_path` is the process cwd fallback. Output is a tmux format string
using `#[fg=...]` directives, so it must be spliced in via `#(...)`.
"""

import json
import os
import re
import sys
import typing as ty
from pathlib import Path

from tools.env import require_env

_COLORS = json.loads(Path(__file__).with_name("colors.json").read_text())
_PALETTE: list[str] = [entry["hex"] for entry in _COLORS["palette"]]
_DIR_COLORS: dict[str, str] = _COLORS["dir_colors"]
_PROCESS_COLORS: dict[str, str] = _COLORS["process_colors"]

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

# Enough of a parent directory to recognize it; the cwd carries the detail.
_PARENT_CHARS = 3



class _Segment(ty.NamedTuple):
    """One path component of a window title, ready to render."""

    text: str
    color: str


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


def _fold_home(path: str) -> str:
    home = os.environ.get("HOME", "")
    if home and (path == home or path.startswith(home + "/")):
        return "~" + path[len(home) :]
    return path


def _normalize_path(path: str) -> str:
    """Strip an OSC 7 `file://host` prefix and fold $HOME to `~`."""
    if path.startswith("file://"):
        without_scheme = path[len("file://") :]
        slash = without_scheme.find("/")
        path = without_scheme[slash:] if slash != -1 else ""
    return _fold_home(path)


# Directories you visit often enough to recognize by a letter or two. An alias stands in
# for the directory's name wherever it would otherwise appear. Aliases are a tmux-only
# shortening, like `_PARENT_CHARS`: wezterm still spells these directories out, and both
# still color them by their real name.
_DIR_ALIASES = {
    _fold_home(path): alias for path, alias in require_env().tmux.dir_aliases.items()
}


def _segment(name: str, text: str | None = None) -> _Segment:
    """Color comes from the full `name`; pass `text` when we render less than that."""
    return _Segment(name if text is None else text, _dir_color(name))


def _parent_path(path: str, parts: ty.Sequence[str]) -> str:
    """`path` minus its last component, spelled the way `_DIR_ALIASES` keys are."""
    joined = "/".join(parts[:-1])
    return "/" + joined if path.startswith("/") else joined


def _display_segments(path: str) -> list[_Segment]:
    path = _normalize_path(path)
    parts = [p for p in path.split("/") if p]
    if not parts:
        return [_segment("/")]
    cwd = parts[-1]
    alias = _DIR_ALIASES.get(path)
    if alias is not None:
        # An alias is already the short name for this place; a parent would only crowd it.
        return [_segment(cwd, alias)]
    if len(parts) == 1:
        return [_segment(cwd, "/" + cwd if path.startswith("/") else cwd)]
    parent = parts[-2]
    parent_text = _DIR_ALIASES.get(_parent_path(path, parts), parent[:_PARENT_CHARS])
    return [_segment(parent, parent_text), _segment(cwd)]


def format_path(path: str) -> str:
    return "/".join(_colored(seg.text, seg.color) for seg in _display_segments(path))


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
