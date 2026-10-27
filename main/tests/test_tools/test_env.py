from pathlib import Path

import pytest

from tools.env import _repo_root
from tools import env


@pytest.mark.parametrize("marker", [".env.toml", ".env.template.toml", ".git"])
def test_repo_root_finds_any_marker_above_the_start(tmp_path: Path, marker: str) -> None:
    (tmp_path / marker).mkdir()
    start = tmp_path / "main" / "src" / "tools"
    start.mkdir(parents=True)

    assert _repo_root(start) == tmp_path


def test_repo_root_accepts_a_git_worktree_file(tmp_path: Path) -> None:
    """A linked worktree's `.git` is a file pointing at the real git dir, not a directory."""
    (tmp_path / ".git").write_text("gitdir: /elsewhere/.git/worktrees/wt\n")

    assert _repo_root(tmp_path / "src") == tmp_path


def test_repo_root_prefers_the_nearest_marker(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    nested = tmp_path / "vendored"
    nested.mkdir()
    (nested / ".env.toml").touch()

    assert _repo_root(nested / "src") == nested


def test_repo_root_raises_when_no_marker_exists(tmp_path: Path) -> None:
    with pytest.raises(EnvironmentError, match="found none of"):
        _repo_root(tmp_path)


@pytest.mark.parametrize("namespace", ["lemons", "claude"])
def test_loads_shared_project_mappings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, namespace: str
) -> None:
    config_file = tmp_path / ".env.toml"
    config_file.write_text(
        f'[{namespace}.project-targets]\nwork-org = "~/work/notes"\n'
        f'[{namespace}.auto-memory-paths]\nwork-org = "~/work"\n'
    )
    monkeypatch.setattr(env, "_ENV_TOML", config_file)

    config = env.load_env()

    assert config is not None
    assert config.lemons.project_targets == {"work-org": Path.home() / "work/notes"}
    assert config.lemons.auto_memory_paths == {"work-org": Path.home() / "work"}


def test_shared_namespace_takes_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_file = tmp_path / ".env.toml"
    config_file.write_text(
        '[lemons.project-targets]\nwork-org = "~/new"\n[claude.project-targets]\nwork-org = "~/old"\n'
    )
    monkeypatch.setattr(env, "_ENV_TOML", config_file)

    config = env.load_env()

    assert config is not None
    assert config.lemons.project_targets == {"work-org": Path.home() / "new"}
