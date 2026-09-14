"""Colored tmux window titles.

A shell window reads `$par/child`, where the parent is shortened to its first three
characters, or to an alias from `_DIR_ALIASES` for the directories you live in. Each
segment takes its color from a hash of its full name, so sibling directories share a
prefix color and shortening a name does not recolor it. A window running a program
reads `program: par/child`, or just `program` for editors and agents whose launch
directory is not what you need to see.

Colors come from `colors.json` beside this module, which `dotfiles/.wezterm.lua`
also reads so wezterm tab titles color the same names the same way. Only the djb2
hash itself is written twice, once per language. Every color there has a dark and
a light value; which one we use comes in as the last argument rather than being
read here, because this runs once per window per status refresh and asking macOS
each time would be felt. `dotfiles/tmux/appearance.sh` does the asking and parks
the answer in the `@appearance` tmux option.

Argv contract (positional, in this order): pane_path, pane_current_path,
pane_current_command, pane_title, appearance. `pane_path` comes from OSC 7 and
wins when set; `pane_current_path` is the process cwd fallback. Output is a tmux
format string using `#[fg=...]` directives, so it must be spliced in via `#(...)`.
"""

import json
import os
import re
import sys
import typing as ty
from pathlib import Path

from tools.env import require_env

Appearance = ty.Literal["dark", "light"]

_COLORS = json.loads(Path(__file__).with_name("colors.json").read_text())


class _Palette(ty.NamedTuple):
    """The colors for one appearance, already narrowed down from colors.json."""

    ordered: list[str]
    dirs: dict[str, str]
    processes: dict[str, str]


def _palette(appearance: Appearance) -> _Palette:
    return _Palette(
        ordered=[entry[appearance] for entry in _COLORS["palette"]],
        dirs={name: c[appearance] for name, c in _COLORS["dir_colors"].items()},
        processes={name: c[appearance] for name, c in _COLORS["process_colors"].items()},
    )


_PALETTES: dict[Appearance, _Palette] = {"dark": _palette("dark"), "light": _palette("light")}

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


def _dir_color(name: str, palette: _Palette) -> str:
    return palette.dirs.get(name, palette.ordered[_djb2(name) % len(palette.ordered)])


def _process_color(name: str, palette: _Palette) -> str:
    return palette.processes.get(name, palette.ordered[_djb2(name) % len(palette.ordered)])


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


def _segment(name: str, palette: _Palette, text: str | None = None) -> _Segment:
    """Color comes from the full `name`; pass `text` when we render less than that."""
    return _Segment(name if text is None else text, _dir_color(name, palette))


def _parent_path(path: str, parts: ty.Sequence[str]) -> str:
    """`path` minus its last component, spelled the way `_DIR_ALIASES` keys are."""
    joined = "/".join(parts[:-1])
    return "/" + joined if path.startswith("/") else joined


def _display_segments(path: str, palette: _Palette) -> list[_Segment]:
    path = _normalize_path(path)
    parts = [p for p in path.split("/") if p]
    if not parts:
        return [_segment("/", palette)]
    cwd = parts[-1]
    alias = _DIR_ALIASES.get(path)
    if alias is not None:
        # An alias is already the short name for this place; a parent would only crowd it.
        return [_segment(cwd, palette, alias)]
    if len(parts) == 1:
        return [_segment(cwd, palette, "/" + cwd if path.startswith("/") else cwd)]
    parent = parts[-2]
    parent_text = _DIR_ALIASES.get(_parent_path(path, parts), parent[:_PARENT_CHARS])
    return [_segment(parent, palette, parent_text), _segment(cwd, palette)]


def format_path(path: str, appearance: Appearance = "dark") -> str:
    segments = _display_segments(path, _PALETTES[appearance])
    return "/".join(_colored(seg.text, seg.color) for seg in segments)


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


def format_window(
    path: str,
    process: str | None = None,
    title: str | None = None,
    appearance: Appearance = "dark",
) -> str:
    program = _resolve_program(process, title, path)
    if program is None:
        return "$" + format_path(path, appearance)
    colored_program = _colored(program, _process_color(program, _PALETTES[appearance]))
    if program in _STANDALONE:
        return colored_program
    return f"{colored_program}: {format_path(path, appearance)}"


def _appearance(value: str | None) -> Appearance:
    """Anything but an explicit "light" is dark, because tmux hands us an empty
    `@appearance` until `dotfiles/tmux/appearance.sh` has run once."""
    return "light" if value == "light" else "dark"


def main(argv: ty.Sequence[str] = sys.argv[1:]) -> None:
    if len(argv) < 2:
        print(
            "usage: tmux-window-status <pane_path> <pane_current_path>"
            " [command] [title] [appearance]",
            file=sys.stderr,
        )
        sys.exit(2)
    pane_path, pane_current_path = argv[0], argv[1]
    process = argv[2] if len(argv) > 2 else None
    title = argv[3] if len(argv) > 3 else None
    appearance = _appearance(argv[4] if len(argv) > 4 else None)
    print(format_window(pane_path or pane_current_path, process, title, appearance))


if __name__ == "__main__":
    main()
