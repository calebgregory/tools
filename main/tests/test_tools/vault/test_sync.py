from pathlib import Path
from unittest.mock import patch

from tools.vault.sync import (
    SyncSummary,
    _classify,
    _discover_files,
    _files_identical,
    _is_binary,
    _is_hidden,
    sync,
)


def _populate(root: Path, files: dict[str, str | bytes]) -> None:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content)


# ---------------------------------------------------------------------------
# _is_hidden
# ---------------------------------------------------------------------------


class TestIsHidden:
    def test_dotfile(self) -> None:
        assert _is_hidden(Path(".DS_Store"))

    def test_dot_directory(self) -> None:
        assert _is_hidden(Path(".obsidian/workspace.json"))

    def test_nested_dot_directory(self) -> None:
        assert _is_hidden(Path("a/.hidden/b.md"))

    def test_normal_file(self) -> None:
        assert not _is_hidden(Path("notes/hello.md"))


# ---------------------------------------------------------------------------
# _discover_files
# ---------------------------------------------------------------------------


class TestDiscoverFiles:
    def test_finds_files_returns_relative_keys(self, tmp_path: Path) -> None:
        _populate(tmp_path, {"a.md": "a", "sub/b.md": "b"})
        found = _discover_files(tmp_path)
        assert set(found.keys()) == {Path("a.md"), Path("sub/b.md")}
        assert all(p.is_absolute() for p in found.values())

    def test_excludes_hidden(self, tmp_path: Path) -> None:
        _populate(tmp_path, {"visible.md": "v", ".hidden": "h", ".obs/x": "x"})
        found = _discover_files(tmp_path)
        assert set(found.keys()) == {Path("visible.md")}

    def test_empty_dir(self, tmp_path: Path) -> None:
        assert _discover_files(tmp_path) == {}

    def test_excludes_directories(self, tmp_path: Path) -> None:
        (tmp_path / "subdir").mkdir()
        assert _discover_files(tmp_path) == {}


# ---------------------------------------------------------------------------
# _is_binary / _files_identical
# ---------------------------------------------------------------------------


class TestFileHelpers:
    def test_text_is_not_binary(self, tmp_path: Path) -> None:
        p = tmp_path / "text.md"
        p.write_text("hello world\n")
        assert not _is_binary(p)

    def test_null_byte_is_binary(self, tmp_path: Path) -> None:
        p = tmp_path / "bin.dat"
        p.write_bytes(b"header\x00binary data")
        assert _is_binary(p)

    def test_identical_files(self, tmp_path: Path) -> None:
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.write_text("same")
        b.write_text("same")
        assert _files_identical(a, b)

    def test_different_files(self, tmp_path: Path) -> None:
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.write_text("one")
        b.write_text("two")
        assert not _files_identical(a, b)


# ---------------------------------------------------------------------------
# _classify
# ---------------------------------------------------------------------------


class TestClassify:
    def test_all_categories(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()

        _populate(
            src,
            {
                "same.md": "hello\n",
                "source_only.md": "only in source\n",
                "diverged.md": "source version\n",
            },
        )
        _populate(
            dst,
            {
                "same.md": "hello\n",
                "dest_only.md": "only in dest\n",
                "diverged.md": "dest version\n",
            },
        )

        src_files = _discover_files(src)
        dst_files = _discover_files(dst)
        actions = _classify(src_files, dst_files, src, dst)

        by_kind = {a.rel.name: a.kind for a in actions}
        assert by_kind == {
            "dest_only.md": "dest_only",
            "diverged.md": "diverged",
            "same.md": "identical",
            "source_only.md": "source_only",
        }

    def test_sorted_by_relative_path(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()
        _populate(src, {"b.md": "b", "a.md": "a"})
        _populate(dst, {"b.md": "b", "a.md": "a"})

        actions = _classify(_discover_files(src), _discover_files(dst), src, dst)
        assert [a.rel.name for a in actions] == ["a.md", "b.md"]

    def test_source_only_fills_dest_path(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()
        _populate(src, {"only.md": "x"})

        actions = _classify(_discover_files(src), _discover_files(dst), src, dst)
        assert actions[0].dest == dst / "only.md"


# ---------------------------------------------------------------------------
# sync() end-to-end
# ---------------------------------------------------------------------------


class TestSyncDryRun:
    def test_dry_run_does_not_modify_files(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()

        _populate(src, {"only_in_src.md": "hello\n"})
        _populate(dst, {"only_in_dst.md": "world\n"})

        summary = sync(src, dst, dry_run=True)

        assert summary.copied_to_dest == 1
        assert summary.copied_to_source == 1
        # files should NOT actually exist in the other directory
        assert not (dst / "only_in_src.md").exists()
        assert not (src / "only_in_dst.md").exists()

    def test_dry_run_all_in_sync(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()
        _populate(src, {"a.md": "same\n"})
        _populate(dst, {"a.md": "same\n"})

        summary = sync(src, dst, dry_run=True)
        assert summary == SyncSummary(0, 0, 0, 1)


class TestSyncInteractive:
    def test_source_only_approve_copies_to_dest(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()
        _populate(src, {"new.md": "new content\n"})

        with patch("builtins.input", return_value="y"):
            summary = sync(src, dst)

        assert (dst / "new.md").read_text() == "new content\n"
        assert summary.copied_to_dest == 1

    def test_source_only_reject_skips(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()
        _populate(src, {"new.md": "new content\n"})

        with patch("builtins.input", return_value="n"):
            summary = sync(src, dst)

        assert not (dst / "new.md").exists()
        assert summary.skipped == 1

    def test_dest_only_approve_copies_to_source(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()
        _populate(dst, {"other.md": "from dest\n"})

        with patch("builtins.input", return_value="y"):
            summary = sync(src, dst)

        assert (src / "other.md").read_text() == "from dest\n"
        assert summary.copied_to_source == 1

    def test_diverged_text_approve_all_hunks(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()
        _populate(src, {"f.md": "line1\nsource\nline3\n"})
        _populate(dst, {"f.md": "line1\ndest\nline3\n"})

        with patch("builtins.input", return_value="a"):
            summary = sync(src, dst)

        expected = "line1\nsource\nline3\n"
        assert (src / "f.md").read_text() == expected
        assert (dst / "f.md").read_text() == expected
        assert summary.merged == 1

    def test_diverged_text_reject_all_hunks_skips(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()
        _populate(src, {"f.md": "line1\nsource\nline3\n"})
        _populate(dst, {"f.md": "line1\ndest\nline3\n"})

        with patch("builtins.input", return_value="n"):
            summary = sync(src, dst)

        # neither file should change
        assert (src / "f.md").read_text() == "line1\nsource\nline3\n"
        assert (dst / "f.md").read_text() == "line1\ndest\nline3\n"
        assert summary.skipped == 1

    def test_diverged_text_partial_hunks(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()

        shared = "".join(f"line{i}\n" for i in range(20))
        src_text = shared.replace("line2\n", "SOURCE_A\n").replace("line17\n", "SOURCE_B\n")
        dst_text = shared.replace("line2\n", "DEST_A\n").replace("line17\n", "DEST_B\n")

        _populate(src, {"f.md": src_text})
        _populate(dst, {"f.md": dst_text})

        # approve first hunk, reject second
        responses = iter(["y", "n"])
        with patch("builtins.input", side_effect=responses):
            summary = sync(src, dst)

        result = (src / "f.md").read_text()
        assert "SOURCE_A" in result
        assert "DEST_B" in result
        # both files should be identical after merge
        assert (dst / "f.md").read_text() == result
        assert summary.merged == 1

    def test_diverged_binary_keep_source(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()
        _populate(src, {"img.png": b"\x89PNG\x00source"})
        _populate(dst, {"img.png": b"\x89PNG\x00dest"})

        with patch("builtins.input", return_value="s"):
            summary = sync(src, dst)

        assert (dst / "img.png").read_bytes() == b"\x89PNG\x00source"
        assert summary.copied_to_dest == 1

    def test_diverged_binary_keep_dest(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()
        _populate(src, {"img.png": b"\x89PNG\x00source"})
        _populate(dst, {"img.png": b"\x89PNG\x00dest"})

        with patch("builtins.input", return_value="d"):
            summary = sync(src, dst)

        assert (src / "img.png").read_bytes() == b"\x89PNG\x00dest"
        assert summary.copied_to_source == 1

    def test_nested_source_only_creates_dirs(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()
        _populate(src, {"a/b/c.md": "deep\n"})

        with patch("builtins.input", return_value="y"):
            sync(src, dst)

        assert (dst / "a/b/c.md").read_text() == "deep\n"

    def test_hidden_files_ignored(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()
        _populate(src, {".obsidian/workspace.json": "{}", ".DS_Store": ""})
        _populate(dst, {"visible.md": "hi\n"})

        with patch("builtins.input", return_value="y"):
            summary = sync(src, dst)

        # only the dest_only visible.md should show up
        assert summary.copied_to_source == 1
        assert summary.copied_to_dest == 0
