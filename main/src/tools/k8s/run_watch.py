#!/usr/bin/env python3
"""Event stream for a running mops pipeline, one line per notable change, for piping
into an agent's Monitor tool (or a terminal).

Emits: newly-troubled pods (deduped so a standing failure alerts once), memory crossing
a share of the node's allocatable, nodes entering Memory/DiskPressure, an all-pending
stall, and a periodic heartbeat carrying job/pod/memory numbers. Exits 0 when the
orchestrator process goes away.

This watcher never kills anything - it reports. k8s-oom-watchdog holds the kill switch and
fires on an observed OOMKilled, because a memory trend extrapolated toward node capacity
is a guess, and acting on it discards real completed work to prevent a failure that
usually never arrives. A short --heartbeat-polls turns the heartbeat into a sampling
trend line, which is how you tell a genuine climb from the sawtooth of allocate-and-flush.

    k8s-run-watch --pid 54451
    k8s-run-watch --pid 54451 --interval 60 --heartbeat-polls 1   # trend sampling
"""

import argparse
import datetime
import sys
import time
import typing as ty

from tools.k8s import _probe


def _emit(message: str) -> None:
    stamp = datetime.datetime.now().isoformat(timespec="seconds")
    print(f"[{stamp}] {message}", flush=True)


class _Armed:
    """One-shot alert that re-arms once the condition clears, so a persistent problem
    reports on each transition instead of on every poll."""

    def __init__(self) -> None:
        self._firing = False

    def should_fire(self, condition_holds: bool) -> bool:
        if not condition_holds:
            self._firing = False
            return False
        if self._firing:
            return False
        self._firing = True
        return True


def _trouble_keys(pods: ty.Sequence[_probe.Pod]) -> dict[str, _probe.Pod]:
    return {f"{pod.name}:{','.join(pod.trouble)}": pod for pod in pods if pod.trouble}


def _heartbeat(
    jobs: ty.Sequence[_probe.Job],
    pods: ty.Sequence[_probe.Pod],
    memory: _probe.MemoryStats | None,
) -> str:
    complete = sum(1 for job in jobs if job.state == "complete")
    running = sum(1 for pod in pods if pod.phase == "Running")
    pending = sum(1 for pod in pods if pod.phase == "Pending")
    troubled = sum(1 for pod in pods if pod.trouble)
    memory_part = (
        f"mem mean {_probe.format_gib(memory.mean_bytes)} max {_probe.format_gib(memory.max_bytes)} "
        f"({memory.worst.pct_of_node:.0f}% of node)"
        if memory
        else "mem unavailable"
    )
    return (
        f"heartbeat: jobs {complete}/{len(jobs)} complete | "
        f"pods {running} running {pending} pending | {memory_part} | trouble {troubled}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True, help="local orchestrator pid to follow")
    parser.add_argument("--namespace", default="caleb-gregory")
    parser.add_argument("--interval", type=int, default=60, help="poll interval seconds")
    parser.add_argument(
        "--memory-pct",
        type=float,
        default=90.0,
        help="warn when a pod exceeds this share of its own node's allocatable memory",
    )
    parser.add_argument(
        "--heartbeat-polls",
        type=int,
        default=15,
        help="emit a heartbeat every N polls; 1 samples every poll for a trend line",
    )
    parser.add_argument(
        "--stall-polls",
        type=int,
        default=25,
        help="warn once if nothing is Running for this many consecutive polls",
    )
    args = parser.parse_args()

    _emit(
        f"watching namespace={args.namespace} pid={args.pid} every {args.interval}s; "
        f"reporting only - k8s-oom-watchdog owns the kill switch"
    )

    seen_trouble: set[str] = set()
    memory_alert = _Armed()
    pressure_alert = _Armed()
    stall_alert = _Armed()
    consecutive_errors = 0
    stalled_polls = 0
    polls = 0

    while True:
        if not _probe.process_alive(args.pid):
            _emit(f"ORCHESTRATOR EXITED: pid {args.pid} is gone - stopping watch")
            sys.exit(0)

        try:
            pods = _probe.get_pods(args.namespace)
            nodes = _probe.get_nodes()
            jobs = _probe.get_jobs(args.namespace)
            consecutive_errors = 0
        except _probe.ProbeError as exc:
            consecutive_errors += 1
            _emit(f"WARN: probe failed ({consecutive_errors} in a row): {exc}")
            time.sleep(min(args.interval * consecutive_errors, 300))
            continue

        current = _trouble_keys(pods)
        fresh = [pod for key, pod in current.items() if key not in seen_trouble]
        seen_trouble.update(current)
        if fresh:
            _emit(f"NEW TROUBLE ({len(fresh)} pod(s)):")
            for pod in fresh[:10]:
                _emit(f"  {pod.name} [{','.join(pod.trouble)}] on {pod.node}: {pod.detail}")
            if len(fresh) > 10:
                _emit(f"  ... and {len(fresh) - 10} more")

        memory = _probe.get_pod_memory(args.namespace, pods, nodes)
        if memory and memory_alert.should_fire(memory.worst.pct_of_node >= args.memory_pct):
            worst = memory.worst
            _emit(
                f"MEMORY {worst.pct_of_node:.0f}% of node allocatable: {worst.pod} at "
                f"{_probe.format_gib(worst.used_bytes)} of "
                f"{_probe.format_gib(worst.node_allocatable_bytes)} on {worst.node} "
                f"({_probe.format_gib(worst.headroom_bytes)} left)"
            )

        under_pressure = [node for node in nodes if node.pressure]
        if pressure_alert.should_fire(bool(under_pressure)):
            _emit(f"NODE PRESSURE on {len(under_pressure)} node(s):")
            for node in under_pressure[:5]:
                _emit(f"  {node.name} {'+'.join(node.pressure)}")

        running = sum(1 for pod in pods if pod.phase == "Running")
        stalled_polls = stalled_polls + 1 if (pods and not running) else 0
        if stall_alert.should_fire(stalled_polls >= args.stall_polls):
            _emit(
                f"STALLED: nothing Running for {stalled_polls} polls "
                f"({len(pods)} pods, {sum(1 for p in pods if p.phase == 'Pending')} pending)"
            )

        polls += 1
        if args.heartbeat_polls > 0 and polls % args.heartbeat_polls == 0:
            _emit(_heartbeat(jobs, pods, memory))

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
