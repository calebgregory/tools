from tools.tmux.session_labels import session_order

from .shared import session


def test_labelled_sessions_keep_their_index_order_not_creation_order() -> None:
    first_created = session(session_id="$1", index_=1)
    second_created = session(session_id="$2", index_=0)

    assert session_order([first_created, second_created]) == [second_created, first_created]


def test_unlabelled_sessions_follow_in_creation_order() -> None:
    new_first = session(session_id="$8")
    labelled = session(session_id="$3", index_=0)
    new_second = session(session_id="$9")

    assert session_order([new_first, labelled, new_second]) == [labelled, new_first, new_second]


def test_a_gap_left_by_a_closed_session_does_not_change_the_order() -> None:
    before_gap = session(session_id="$1", index_=0)
    after_gap = session(session_id="$3", index_=2)

    assert session_order([before_gap, after_gap]) == [before_gap, after_gap]


def test_hidden_sessions_are_left_out() -> None:
    shown = session(session_id="$1", name="notes", index_=0)
    hidden = session(session_id="$2", name="_lma_grove", index_=1)

    assert session_order([shown, hidden]) == [shown]
