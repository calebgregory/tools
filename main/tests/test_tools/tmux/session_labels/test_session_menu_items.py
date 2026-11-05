from tools.tmux.session_labels import SessionLabel, session_menu_items


def test_session_menu_items_give_name_number_key_and_switch_command_per_session() -> None:
    labels = [
        SessionLabel("$4", "notes", 0, "#DARK0", "#LIGHT0"),
        SessionLabel("$7", "a#b", 1, "#DARK1", "#LIGHT1"),
    ]

    result = session_menu_items(labels)

    assert result == [
        "#{?#{==:#{session_id},$4},#[bold],}0: #[fg=#{?#{==:#{@appearance},light},##LIGHT0,##DARK0}]notes",
        "0",
        "switch-client -t '$4'",
        "#{?#{==:#{session_id},$7},#[bold],}1: #[fg=#{?#{==:#{@appearance},light},##LIGHT1,##DARK1}]a##b",
        "1",
        "switch-client -t '$7'",
    ]


def test_session_menu_items_have_no_key_past_nine() -> None:
    result = session_menu_items([SessionLabel("$1", "s", 10, "#D", "#L")])

    assert result[1] == ""


def test_session_menu_items_with_no_sessions() -> None:
    assert session_menu_items([]) == []
