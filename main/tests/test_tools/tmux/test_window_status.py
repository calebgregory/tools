import pytest

from tools.tmux import window_status
from tools.tmux.window_status import format_path, format_window

_HOME = "/Users/someone"


@pytest.fixture(autouse=True)
def _home(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", _HOME)


def _dir(name: str) -> str:
    return f"#[fg={window_status._dir_color(name)}]{name}#[fg=default]"


def _program(name: str) -> str:
    return f"#[fg={window_status._process_color(name)}]{name}#[fg=default]"


@pytest.mark.parametrize(
    ("path", "segments"),
    [
        (f"{_HOME}/tools/lemonaid", ["tools", "lemonaid"]),
        (f"{_HOME}/tools", ["~", "tools"]),
        (_HOME, ["~"]),
        (f"{_HOME}sfx/tools", ["someonesfx", "tools"]),
        (f"file://host.local{_HOME}/work/apps/foo", ["apps", "foo"]),
        ("/opt/homebrew/bin", ["homebrew", "bin"]),
        ("/tmp", ["/tmp"]),
        ("/", ["/"]),
        ("", ["/"]),
    ],
)
def test_format_path_shows_parent_and_child(path: str, segments: list[str]) -> None:
    assert format_path(path) == "/".join(_dir(seg) for seg in segments)


def test_parent_color_differs_while_child_color_is_shared() -> None:
    in_tools = format_path(f"{_HOME}/tools/lemonaid")
    in_play = format_path(f"{_HOME}/play/lemonaid")

    assert in_tools != in_play
    assert in_tools.endswith(_dir("lemonaid"))
    assert in_play.endswith(_dir("lemonaid"))


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
