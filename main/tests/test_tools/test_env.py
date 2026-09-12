from pathlib import Path

import pytest

from tools.env import _repo_root


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
