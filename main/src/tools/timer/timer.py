#!/usr/bin/env python

import sys
import termios
import threading
import tty
from time import monotonic, sleep


def _watch_spacebar(paused: threading.Event) -> None:
    """Toggle `paused` each time the spacebar is pressed.

    Runs on a daemon thread and relies on the caller having put the terminal in
    cbreak mode so single keypresses arrive without a trailing Enter.
    """
    while True:
        ch = sys.stdin.read(1)
        if ch == " ":
            if paused.is_set():
                paused.clear()
            else:
                paused.set()


def _run_timer(paused: threading.Event) -> None:
    accumulated = 0.0  # seconds elapsed before the current running segment
    segment_start = monotonic()  # monotonic time the current running segment began

    was_paused = False
    while True:
        sleep(0.1)
        is_paused = paused.is_set()

        if is_paused and not was_paused:
            accumulated += monotonic() - segment_start
        elif not is_paused and was_paused:
            segment_start = monotonic()
        was_paused = is_paused

        elapsed = accumulated if is_paused else accumulated + (monotonic() - segment_start)
        min, sec = divmod(int(elapsed), 60)
        marker = "☽" if is_paused else " "

        sys.stdout.write(f"\r{min:02d}:{sec:02d} {marker}")
        sys.stdout.flush()


def main() -> None:
    fd = sys.stdin.fileno()
    old_termios = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    paused = threading.Event()
    threading.Thread(target=_watch_spacebar, args=(paused,), daemon=True).start()

    print("space to pause/resume, ctrl-c to quit")

    try:
        _run_timer(paused)
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_termios)
        print()


if __name__ == "__main__":
    main()
