#!/usr/bin/env python

import queue
import sys
import termios
import threading
import tty
import typing as ty
from dataclasses import dataclass
from time import monotonic, sleep


def _watch_keys(keys: queue.Queue[str]) -> None:
    """Forward each keypress onto `keys`.

    Runs on a daemon thread and relies on the caller having put the terminal in cbreak mode so single
    keypresses arrive without a trailing Enter.
    """
    while True:
        keys.put(sys.stdin.read(1))


@dataclass
class _TimerState:
    accumulated: float = 0.0  # seconds banked before the current running segment
    segment_start: float = 0.0  # monotonic time the current running segment began
    paused: bool = False


def _elapsed(state: _TimerState) -> float:
    if state.paused:
        return state.accumulated
    return state.accumulated + (monotonic() - state.segment_start)


def _toggle_pause(state: _TimerState) -> _TimerState:
    if state.paused:
        state.segment_start = monotonic()  # resume: begin a fresh segment
    else:
        state.accumulated += monotonic() - state.segment_start  # pause: bank the segment
    state.paused = not state.paused
    return state


def _reset(state: _TimerState) -> _TimerState:
    state.accumulated = 0.0
    state.segment_start = monotonic()
    return state


_COMMANDS: ty.Final[dict[str, ty.Callable[[_TimerState], _TimerState]]] = {
    " ": _toggle_pause,
    "r": _reset,
}


def _run_timer(keys: queue.Queue[str]) -> None:
    state = _TimerState(segment_start=monotonic())
    while True:
        sleep(0.1)

        while True:
            try:
                ch = keys.get_nowait()
            except queue.Empty:
                break
            if command := _COMMANDS.get(ch):
                state = command(state)

        min, sec = divmod(int(_elapsed(state)), 60)
        marker = "☽" if state.paused else " "

        sys.stdout.write(f"\r{min:02d}:{sec:02d} {marker}")
        sys.stdout.flush()


def main() -> None:
    fd = sys.stdin.fileno()
    old_termios = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    keys: queue.Queue[str] = queue.Queue()
    threading.Thread(target=_watch_keys, args=(keys,), daemon=True).start()

    print("space to pause/resume, r to reset, ctrl-c to quit")

    try:
        _run_timer(keys)
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_termios)
        print()


if __name__ == "__main__":
    main()
