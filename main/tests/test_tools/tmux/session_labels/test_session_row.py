from tools.tmux.session_labels import SessionLabel, session_row


def test_session_row_bakes_id_number_name_and_both_colors_per_session_with_hashes_escaped() -> None:
    labels = [
        SessionLabel("$4", "notes", 0, "#DARK0", "#LIGHT0"),
        SessionLabel("$7", "tools", 1, "#DARK1", "#LIGHT1"),
    ]

    result = session_row(labels)

    color0 = "#{?#{==:#{@appearance},light},##LIGHT0,##DARK0}"
    color1 = "#{?#{==:#{@appearance},light},##LIGHT1,##DARK1}"
    assert result == (
        "#[align=left]"
        f"#[range=session|$4]#{{?#{{==:#{{session_id}},$4}},#[bold#,underscore#,us={color0}],}}"
        f" 0: #[fg={color0}]notes#[fg=default] #[norange default] "
        f"#[range=session|$7]#{{?#{{==:#{{session_id}},$7}},#[bold#,underscore#,us={color1}],}}"
        f" 1: #[fg={color1}]tools#[fg=default] #[norange default] "
    )


def test_session_row_escapes_hashes_in_names() -> None:
    result = session_row([SessionLabel("$1", "a#b", 0, "#D", "#L")])

    assert "]a##b#[fg=default]" in result


def test_session_row_with_no_sessions() -> None:
    assert session_row([]) == "#[align=left]"
