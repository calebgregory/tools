import pytest

from tools.tmux.session_labels import moved

from .shared import session

_A, _B, _C = (session(session_id=f"${n}", index_=n) for n in range(3))


@pytest.mark.parametrize(
    ("session_id", "position", "expected"),
    [
        ("$2", 0, [_C, _A, _B]),
        ("$0", 2, [_B, _C, _A]),
        ("$0", 1, [_B, _A, _C]),
        ("$1", 1, [_A, _B, _C]),
        ("$0", 99, [_B, _C, _A]),
        ("$2", -5, [_C, _A, _B]),
    ],
)
def test_moved_puts_the_session_at_the_position_and_clamps(session_id: str, position: int, expected: list) -> None:
    assert moved([_A, _B, _C], session_id, position) == expected


def test_moved_rejects_an_unknown_session() -> None:
    with pytest.raises(ValueError, match=r"\$7"):
        moved([_A, _B], "$7", 0)
