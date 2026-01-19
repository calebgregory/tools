#!/usr/bin/env -S uv run python
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class Silence:
    start: float
    end: float

    @property
    def mid(self) -> float:
        return (self.start + self.end) / 2.0


SILENCE_START_RE = re.compile(r"silence_start:\s*([0-9]+(?:\.[0-9]+)?)")
SILENCE_END_RE = re.compile(r"silence_end:\s*([0-9]+(?:\.[0-9]+)?)")


def parse_silences(lines: Iterable[str]) -> List[Silence]:
    silences: List[Silence] = []
    current_start: Optional[float] = None

    for line in lines:
        if m1 := SILENCE_START_RE.search(line):
            current_start = float(m1.group(1))
            continue

        if m2 := SILENCE_END_RE.search(line):
            end = float(m2.group(1))
            if current_start is None:
                # Occasionally logs can be truncated; ignore unmatched end.
                continue
            if end >= current_start:
                silences.append(Silence(start=current_start, end=end))
            current_start = None

    return silences


def choose_cuts(
    mids: List[float],
    every: float,
    duration: Optional[float],
    window: Optional[float],
    start_at: float,
    stop_before_end: float,
) -> List[Tuple[float, float, float]]:
    """
    Returns list of (target, chosen_mid, delta) where delta = chosen_mid - target
    """
    if not mids:
        return []

    mids_sorted = sorted(mids)
    used = set()

    # If duration is not provided, infer something reasonable from the last midpoint.
    inferred_duration = mids_sorted[-1] + every
    dur = duration if duration is not None else inferred_duration

    # Targets: start_at + k*every, but don't schedule a cut too close to end
    last_target = dur - stop_before_end
    t = start_at

    results: List[Tuple[float, float, float]] = []
    while t <= last_target:
        # candidate mids
        if window is None:
            candidates = [(abs(m - t), m) for m in mids_sorted]
        else:
            candidates = [(abs(m - t), m) for m in mids_sorted if abs(m - t) <= window]

        candidates.sort(key=lambda x: x[0])

        chosen: Optional[float] = None
        for _, m in candidates:
            if m not in used:
                chosen = m
                break

        if chosen is None:
            # No unused candidate within the window. If window was set, fall back to global nearest unused.
            if window is not None:
                candidates2 = [(abs(m - t), m) for m in mids_sorted if m not in used]
                candidates2.sort(key=lambda x: x[0])
                if candidates2:
                    chosen = candidates2[0][1]

        if chosen is None:
            break

        used.add(chosen)
        results.append((t, chosen, chosen - t))
        t += every

    return results


def fmt_float(x: float, digits: int) -> str:
    return f"{x:.{digits}f}".rstrip("0").rstrip(".")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Pick silence midpoints nearest to every N seconds for ffmpeg segmentation."
    )
    ap.add_argument("log", help="Path to ffmpeg silencedetect log file")
    ap.add_argument(
        "--every", type=float, default=1200.0, help="Target interval in seconds (default: 1200=20m)"
    )
    ap.add_argument(
        "--duration", type=float, default=None, help="Total media duration in seconds (optional)"
    )
    ap.add_argument(
        "--window",
        type=float,
        default=90.0,
        help="Only consider silences within +/- window seconds of target. Use 0 to disable (default: 90)",
    )
    ap.add_argument(
        "--start-at",
        type=float,
        default=None,
        help="First target cut time in seconds (default: every)",
    )
    ap.add_argument(
        "--stop-before-end",
        type=float,
        default=30.0,
        help="Don't place a cut within this many seconds of the end (default: 30)",
    )
    ap.add_argument(
        "--digits",
        type=int,
        default=6,
        help="Decimal precision for output times (default: 6)",
    )
    ap.add_argument(
        "--format",
        choices=["segment_times", "lines", "jsonlike"],
        default="segment_times",
        help="Output format (default: segment_times)",
    )
    args = ap.parse_args()

    window = None if args.window == 0 else args.window
    start_at = args.start_at if args.start_at is not None else args.every

    with open(args.log, "r", encoding="utf-8", errors="replace") as f:
        silences = parse_silences(f)

    mids = [s.mid for s in silences]
    picks = choose_cuts(
        mids=mids,
        every=args.every,
        duration=args.duration,
        window=window,
        start_at=start_at,
        stop_before_end=args.stop_before_end,
    )

    if not silences:
        print("No silence intervals found in log.", file=sys.stderr)
        sys.exit(2)

    if not picks:
        print(
            "No cut points could be selected (try increasing --window or check your log).", file=sys.stderr
        )
        sys.exit(3)

    # Print a helpful summary to stderr
    print(f"Found {len(silences)} silence intervals.", file=sys.stderr)
    print(f"Selected {len(picks)} cut points near every {args.every:.0f}s.", file=sys.stderr)
    if window is not None:
        print(f"Window: +/- {window:.0f}s (fallback to global nearest if needed).", file=sys.stderr)

    cuts = [chosen for (_, chosen, _) in picks]

    if args.format == "segment_times":
        # comma-separated, perfect for ffmpeg -segment_times
        print(",".join(fmt_float(c, args.digits) for c in cuts))
    elif args.format == "lines":
        for target, chosen, delta in picks:
            print(
                f"target={fmt_float(target, args.digits)} chosen={fmt_float(chosen, args.digits)} delta={fmt_float(delta, args.digits)}"
            )
    else:  # jsonlike
        print("[")
        for target, chosen, delta in picks:
            print(
                f'  {{"target": {fmt_float(target, args.digits)}, "cut": {fmt_float(chosen, args.digits)}, "delta": {fmt_float(delta, args.digits)}}},'
            )
        print("]")


if __name__ == "__main__":
    main()
