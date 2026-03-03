from pathlib import Path

from tools.diff import apply_hunks, diff, hunks


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text)
    return p


# ---------------------------------------------------------------------------
# hunks()
# ---------------------------------------------------------------------------


class TestHunks:
    def test_single_hunk(self, tmp_path: Path) -> None:
        v1 = _write(tmp_path, "v1.md", "a\nb\nc\n")
        v2 = _write(tmp_path, "v2.md", "a\nX\nc\n")
        h = hunks(diff(v1, v2))
        assert len(h) == 1
        assert h[0].header.startswith("@@")

    def test_two_hunks_from_distant_changes(self, tmp_path: Path) -> None:
        # changes separated by >6 equal lines → 2 hunks (context=3 on each side)
        shared = [f"line{i}\n" for i in range(20)]
        v1_lines = shared.copy()
        v2_lines = shared.copy()
        v1_lines[2] = "SOURCE_A\n"
        v2_lines[2] = "DEST_A\n"
        v1_lines[17] = "SOURCE_B\n"
        v2_lines[17] = "DEST_B\n"

        v1 = _write(tmp_path, "v1.md", "".join(v1_lines))
        v2 = _write(tmp_path, "v2.md", "".join(v2_lines))
        h = hunks(diff(v1, v2))
        assert len(h) == 2

    def test_no_diff_returns_empty(self, tmp_path: Path) -> None:
        v1 = _write(tmp_path, "v1.md", "same\n")
        v2 = _write(tmp_path, "v2.md", "same\n")
        assert hunks(diff(v1, v2)) == []


# ---------------------------------------------------------------------------
# apply_hunks()
# ---------------------------------------------------------------------------


class TestApplyHunks:
    def test_approve_all_matches_source(self) -> None:
        dest = ["a\n", "DEST\n", "c\n"]
        source = ["a\n", "SOURCE\n", "c\n"]
        result = apply_hunks(dest, source, [True])
        assert result == source

    def test_reject_all_matches_dest(self) -> None:
        dest = ["a\n", "DEST\n", "c\n"]
        source = ["a\n", "SOURCE\n", "c\n"]
        result = apply_hunks(dest, source, [False])
        assert result == dest

    def test_partial_approval_two_hunks(self) -> None:
        shared = [f"line{i}\n" for i in range(20)]
        dest = shared.copy()
        source = shared.copy()
        dest[2] = "DEST_A\n"
        source[2] = "SOURCE_A\n"
        dest[17] = "DEST_B\n"
        source[17] = "SOURCE_B\n"

        # approve first hunk only
        result = apply_hunks(dest, source, [True, False])
        assert "SOURCE_A\n" in result
        assert "DEST_B\n" in result
        assert "DEST_A\n" not in result
        assert "SOURCE_B\n" not in result

    def test_partial_approval_reverse(self) -> None:
        shared = [f"line{i}\n" for i in range(20)]
        dest = shared.copy()
        source = shared.copy()
        dest[2] = "DEST_A\n"
        source[2] = "SOURCE_A\n"
        dest[17] = "DEST_B\n"
        source[17] = "SOURCE_B\n"

        # approve second hunk only
        result = apply_hunks(dest, source, [False, True])
        assert "DEST_A\n" in result
        assert "SOURCE_B\n" in result

    def test_mismatched_approval_length_raises(self) -> None:
        import pytest

        dest = ["a\n", "DEST\n", "c\n"]
        source = ["a\n", "SOURCE\n", "c\n"]
        with pytest.raises(ValueError, match="expected 1 approval flags, got 3"):
            apply_hunks(dest, source, [True, False, True])

    def test_insertion_hunk(self) -> None:
        dest = ["a\n", "c\n"]
        source = ["a\n", "b\n", "c\n"]
        result = apply_hunks(dest, source, [True])
        assert result == source

    def test_deletion_hunk(self) -> None:
        dest = ["a\n", "b\n", "c\n"]
        source = ["a\n", "c\n"]
        result = apply_hunks(dest, source, [True])
        assert result == source

    def test_identical_is_no_op(self) -> None:
        lines = ["a\n", "b\n", "c\n"]
        # no hunks → empty approved list
        result = apply_hunks(lines, lines, [])
        assert result == lines
