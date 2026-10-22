from tools.tmux.session_index import IndexAssignment, index_assignments


def test_index_assignments_number_sessions_in_list_order() -> None:
    result = index_assignments(["$4", "$0", "$9"])

    assert result == [
        IndexAssignment("$4", 0),
        IndexAssignment("$0", 1),
        IndexAssignment("$9", 2),
    ]


def test_index_assignments_with_no_sessions() -> None:
    assert index_assignments([]) == []
