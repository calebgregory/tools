#!/usr/bin/env python3
"""One-shot snapshot of a running mops pipeline: job tallies, pod phases, failures,
memory against each pod's own node allocatable, and node pressure.

Answers "is this run healthy, and how much headroom is left" in a single call, so
triaging a monitor alert doesn't mean reassembling kubectl and jq one-liners.

Read-only. The kill switch lives only in k8s-oom-watchdog, which fires on an observed
OOMKilled rather than on a projected trend.

    k8s-run-status --pid 54451
    k8s-run-status --pid 54451 --namespace caleb-gregory --stragglers 10
"""

import argparse
import collections
import sys
import textwrap
import typing as ty

from tools.k8s import _probe


def _job_line(jobs: ty.Sequence[_probe.Job]) -> str:
    if not jobs:
        return "no jobs (completed jobs are garbage-collected on their TTL)"
    by_state = collections.Counter(job.state for job in jobs)
    parts = [f"{count} {state}" for state, count in sorted(by_state.items())]
    retried = sum(1 for job in jobs if job.failed_pods and job.state == "complete")
    suffix = f"; {retried} succeeded only after a retry" if retried else ""
    return f"{len(jobs)} total: {', '.join(parts)}{suffix}"


def _pod_line(pods: ty.Sequence[_probe.Pod]) -> str:
    if not pods:
        return "no pods"
    by_phase = collections.Counter(pod.phase for pod in pods)
    return f"{len(pods)} total: " + ", ".join(
        f"{count} {phase.lower()}" for phase, count in sorted(by_phase.items())
    )


def _trouble_lines(pods: ty.Sequence[_probe.Pod]) -> list[str]:
    troubled = [pod for pod in pods if pod.trouble]
    if not troubled:
        return ["none"]

    by_kind = collections.Counter(kind for pod in troubled for kind in pod.trouble)
    lines = [", ".join(f"{count} {kind}" for kind, count in sorted(by_kind.items()))]

    by_node = collections.Counter(pod.node for pod in troubled)
    if len(by_node) == 1:
        node, count = next(iter(by_node.items()))
        lines.append(f"all {count} on one node ({node}) - likely that node, not the workload")
    else:
        worst = ", ".join(f"{node} x{count}" for node, count in by_node.most_common(3))
        lines.append(f"spread over {len(by_node)} nodes; worst: {worst}")

    lines.extend(f"  {pod.name}: {pod.detail or ','.join(pod.trouble)}" for pod in troubled[:5])
    if len(troubled) > 5:
        lines.append(f"  ... and {len(troubled) - 5} more")
    return lines


def _memory_lines(stats: _probe.MemoryStats | None, pods: ty.Sequence[_probe.Pod]) -> list[str]:
    if stats is None:
        if not any(pod.phase == "Running" for pod in pods):
            return ["no running pods to measure"]
        return ["unavailable (metrics-server not responding)"]
    worst = stats.worst
    lines = [
        f"n={stats.samples}  mean {_probe.format_gib(stats.mean_bytes)}  "
        f"p50 {_probe.format_gib(stats.p50_bytes)}  "
        f"p90 {_probe.format_gib(stats.p90_bytes)}  "
        f"max {_probe.format_gib(stats.max_bytes)}"
    ]
    if worst.node_allocatable_bytes:
        lines.append(
            f"worst pod {worst.pct_of_node:.0f}% of its node's "
            f"{_probe.format_gib(worst.node_allocatable_bytes)} allocatable "
            f"({_probe.format_gib(worst.headroom_bytes)} headroom): {worst.pod}"
        )
    return lines


def _node_line(nodes: ty.Sequence[_probe.Node]) -> str:
    under = [node for node in nodes if node.pressure]
    if not under:
        return f"{len(nodes)} total, none under Memory/DiskPressure"
    detail = ", ".join(f"{node.name} ({'+'.join(node.pressure)})" for node in under[:5])
    return f"{len(nodes)} total, {len(under)} under pressure: {detail}"


def _straggler_lines(pods: ty.Sequence[_probe.Pod], limit: int) -> list[str]:
    running = sorted(
        (pod for pod in pods if pod.phase == "Running"), key=lambda p: p.age_seconds, reverse=True
    )
    if not running:
        return ["none running"]
    return [f"  {pod.name}  {pod.age_seconds // 60}m" for pod in running[:limit]] + (
        [f"  ... and {len(running) - limit} more"] if len(running) > limit else []
    )


def _render(
    pid: int,
    namespace: str,
    alive: bool,
    elapsed: str,
    jobs: ty.Sequence[_probe.Job],
    pods: ty.Sequence[_probe.Pod],
    nodes: ty.Sequence[_probe.Node],
    memory: _probe.MemoryStats | None,
    stragglers: int,
) -> str:
    orchestrator = f"alive, up {elapsed}" if alive else "GONE"
    indent = "\n          "
    return textwrap.dedent(
        f"""
        orchestrator  pid {pid} - {orchestrator}
        namespace     {namespace}

        jobs      {_job_line(jobs)}
        pods      {_pod_line(pods)}
        trouble   {indent.join(_trouble_lines(pods))}
        memory    {indent.join(_memory_lines(memory, pods))}
        nodes     {_node_line(nodes)}

        longest-running pods
        {chr(10).join(_straggler_lines(pods, stragglers))}
        """
    ).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True, help="local orchestrator pid")
    parser.add_argument("--namespace", default="caleb-gregory")
    parser.add_argument(
        "--stragglers", type=int, default=5, help="how many longest-running pods to list"
    )
    args = parser.parse_args()

    try:
        pods = _probe.get_pods(args.namespace)
        nodes = _probe.get_nodes()
        jobs = _probe.get_jobs(args.namespace)
    except _probe.ProbeError as exc:
        print(f"probe failed: {exc}", file=sys.stderr)
        sys.exit(2)

    print(
        _render(
            pid=args.pid,
            namespace=args.namespace,
            alive=_probe.process_alive(args.pid),
            elapsed=_probe.process_elapsed(args.pid),
            jobs=jobs,
            pods=pods,
            nodes=nodes,
            memory=_probe.get_pod_memory(args.namespace, pods, nodes),
            stragglers=args.stragglers,
        )
    )


if __name__ == "__main__":
    main()
