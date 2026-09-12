import json
import pathlib

import pytest

from tools.tmux import window_status
from tools.tmux.window_status import format_path, format_window

_HOME = "/Users/someone"


@pytest.fixture(autouse=True)
def _home(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", _HOME)


def _dir(name: str, text: str | None = None) -> str:
    """A rendered segment: colored by the full `name`, showing `text` when it is shortened."""
    return f"#[fg={window_status._dir_color(name)}]{name if text is None else text}#[fg=default]"


def _program(name: str) -> str:
    return f"#[fg={window_status._process_color(name)}]{name}#[fg=default]"


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (f"{_HOME}/tools/lemonaid", _dir("tools", "too") + "/" + _dir("lemonaid")),
        (f"{_HOME}/tools", _dir("~") + "/" + _dir("tools")),
        (_HOME, _dir("~")),
        (f"{_HOME}sfx/tools", _dir("someonesfx", "som") + "/" + _dir("tools")),
        (f"file://host.local{_HOME}/work/apps/foo", _dir("apps", "app") + "/" + _dir("foo")),
        ("/opt/homebrew/bin", _dir("homebrew", "hom") + "/" + _dir("bin")),
        ("/tmp", _dir("tmp", "/tmp")),
        ("/", _dir("/")),
        ("", _dir("/")),
    ],
)
def test_format_path_shortens_parent_to_three_characters(path: str, expected: str) -> None:
    assert format_path(path) == expected


def test_parent_color_survives_shortening() -> None:
    """`tools` and `too` hash differently, so the color must come from the full name."""
    result = format_path(f"{_HOME}/tools/lemonaid")

    assert result.startswith(f"#[fg={window_status._dir_color('tools')}]too#[fg=default]")
    assert window_status._dir_color("too") != window_status._dir_color("tools")


@pytest.fixture
def _aliases(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        window_status, "_DIR_ALIASES", {"~/work/notes/personal-work": "w", "~/work/wt": "mt"}
    )


@pytest.mark.parametrize(
    ("path", "expected_texts"),
    [
        (f"{_HOME}/work/notes/personal-work", ["w"]),
        (f"{_HOME}/work/wt", ["mt"]),
        (f"{_HOME}/work/wt/main", ["mt", "main"]),
        (f"{_HOME}/work/wt/main/src", ["mai", "src"]),
        (f"{_HOME}/work/notes/personal", ["not", "personal"]),
    ],
)
def test_alias_replaces_a_directory_name(
    _aliases: None, path: str, expected_texts: list[str]
) -> None:
    assert [seg.text for seg in window_status._display_segments(path)] == expected_texts


def test_aliased_directory_keeps_the_color_of_its_real_name(_aliases: None) -> None:
    result = format_path(f"{_HOME}/work/wt/main")

    assert result.startswith(f"#[fg={window_status._dir_color('wt')}]mt#[fg=default]")


def test_parent_color_differs_while_child_color_is_shared() -> None:
    in_tools = format_path(f"{_HOME}/tools/lemonaid")
    in_play = format_path(f"{_HOME}/play/lemonaid")

    assert in_tools != in_play
    assert in_tools.endswith(_dir("lemonaid"))
    assert in_play.endswith(_dir("lemonaid"))


def test_colors_match_the_shared_palette_file() -> None:
    shared = json.loads((pathlib.Path(window_status.__file__).parent / "colors.json").read_text())

    assert window_status._PALETTE == [entry["hex"] for entry in shared["palette"]]
    assert window_status._dir_color("apps") == shared["dir_colors"]["apps"]


@pytest.mark.parametrize("shell", ["zsh", "bash", "fish", "xonsh", "mise", "starship", None, ""])
def test_shell_window_is_dollar_path(shell: str | None) -> None:
    assert format_window(f"{_HOME}/tools/main", shell) == "$" + format_path(f"{_HOME}/tools/main")


@pytest.mark.parametrize("program", ["claude", "emacs", "emacsclient", "nvim", "lma", "htop"])
def test_standalone_program_shows_name_only(program: str) -> None:
    assert format_window(f"{_HOME}/tools/main", program) == _program(program)


def test_version_string_process_is_claude() -> None:
    assert format_window(f"{_HOME}/tools/main", "2.1.12") == _program("claude")


def test_other_program_shows_name_and_path() -> None:
    path = f"{_HOME}/tools/main"

    result = format_window(path, "git")

    assert result == f"{_program('git')}: {format_path(path)}"


@pytest.mark.parametrize(
    ("process", "title", "expected_program"),
    [
        ("python3.13", "myapp - host", "myapp"),
        ("node", "vite dev", "vite"),
        ("node22", None, "node22"),
        ("ruby", "", "ruby"),
    ],
)
def test_interpreter_prefers_title(process: str, title: str | None, expected_program: str) -> None:
    path = f"{_HOME}/tools/main"

    result = format_window(path, process, title)

    assert result == f"{_program(expected_program)}: {format_path(path)}"


def test_interpreter_title_naming_a_standalone_app_shows_name_only() -> None:
    assert format_window(f"{_HOME}/tools/main", "python3", "lma") == _program("lma")


@pytest.mark.parametrize(
    "title",
    [None, "", "~/tools/main", "/Users/someone", "me@host:~", "zsh", "-zsh", "main"],
)
def test_python_without_informative_title_is_a_shell(title: str | None) -> None:
    path = f"{_HOME}/tools/main"

    result = format_window(path, "python3.12", title)

    assert result == "$" + format_path(path)


def test_main_prefers_osc7_path_over_cwd(capsys: pytest.CaptureFixture[str]) -> None:
    window_status.main([f"{_HOME}/a/b", f"{_HOME}/stale/c", "zsh", ""])

    assert capsys.readouterr().out.strip() == "$" + format_path(f"{_HOME}/a/b")


def test_main_falls_back_to_cwd_when_osc7_path_is_empty(capsys: pytest.CaptureFixture[str]) -> None:
    window_status.main(["", f"{_HOME}/stale/c", "zsh", ""])

    assert capsys.readouterr().out.strip() == "$" + format_path(f"{_HOME}/stale/c")
