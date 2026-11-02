from tools.tmux.session_labels import Session


def session(*, session_id: str = "$0", name: str = "s", index_: int | None = None) -> Session:
    return Session(session_id=session_id, name=name, index_=index_)
