#!/usr/bin/env python3
"""Read-only kubectl probes shared by the run-monitoring commands in this directory.

Stdlib-only, so the `k8s-*` commands stay importable and runnable wherever kubectl is.

Nothing in this module kills anything, and neither do its callers. oom_watchdog.py owns
the kill switch, and it triggers on an observed OOMKilled rather than on a projected
trend. Extrapolating a memory growth rate is not evidence a run is failing.
"""

import argparse
import datetime
import json
import re
import subprocess
import typing as ty

_BINARY_SUFFIXES = {"Ki": 1024, "Mi": 1024**2, "Gi": 1024**3, "Ti": 1024**4, "Pi": 1024**5}
_DECIMAL_SUFFIXES = {"K": 1000, "M": 1000**2, "G": 1000**3, "T": 1000**4, "P": 1000**5}

GIB = 1024**3

TroubleKind = ty.Literal["oomkilled", "evicted", "nonzero_exit", "crashloop", "image_pull", "create_error"]
JobState = ty.Literal["complete", "failed", "active"]

_WAITING_TROUBLE: dict[str, TroubleKind] = {
    "CrashLoopBackOff": "crashloop",
    "ImagePullBackOff": "image_pull",
    "ErrImagePull": "image_pull",
    "CreateContainerError": "create_error",
    "CreateContainerConfigError": "create_error",
}


class ProbeError(RuntimeError):
    """kubectl was unreachable or returned something unparseable."""


def parse_quantity(value: str) -> int:
    """Kubernetes resource quantity to bytes, e.g. '258632268Ki', '248G', '1910442199973'.

    Binary suffixes are checked before decimal ones so 'Ki' is not read as 'K'.
    """
    text = value.strip()
    for suffix, multiplier in (*_BINARY_SUFFIXES.items(), *_DECIMAL_SUFFIXES.items()):
        if text.endswith(suffix):
            return int(float(text[: -len(suffix)]) * multiplier)
    return int(float(text))


def format_gib(num_bytes: int) -> str:
    return f"{num_bytes / GIB:.1f}Gi"


def _kubectl_json(args: ty.Sequence[str], timeout: int = 60) -> dict:
    try:
        completed = subprocess.run(
            ["kubectl", *args, "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
        raise ProbeError(f"kubectl {' '.join(args)} failed: {exc}") from exc
    try:
        return dict(json.loads(completed.stdout))
    except json.JSONDecodeError as exc:
        raise ProbeError(f"kubectl {' '.join(args)} returned non-JSON: {exc}") from exc


def _parse_rfc3339(stamp: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00"))


class Pod(ty.NamedTuple):
    name: str
    node: str
    phase: str
    age_seconds: int
    trouble: tuple[TroubleKind, ...]
    detail: str


class Node(ty.NamedTuple):
    name: str
    allocatable_memory_bytes: int
    pressure: tuple[str, ...]


class Job(ty.NamedTuple):
    name: str
    state: JobState
    failed_pods: int


class PodMemory(ty.NamedTuple):
    pod: str
    node: str
    used_bytes: int
    node_allocatable_bytes: int

    @property
    def pct_of_node(self) -> float:
        if not self.node_allocatable_bytes:
            return 0.0
        return 100.0 * self.used_bytes / self.node_allocatable_bytes

    @property
    def headroom_bytes(self) -> int:
        return max(0, self.node_allocatable_bytes - self.used_bytes)


class MemoryStats(ty.NamedTuple):
    samples: int
    p50_bytes: int
    p90_bytes: int
    max_bytes: int
    mean_bytes: int
    worst: PodMemory


def _pod_trouble(pod: dict) -> tuple[tuple[TroubleKind, ...], str]:
    kinds: list[TroubleKind] = []
    details: list[str] = []

    if (pod.get("status") or {}).get("reason") == "Evicted":
        kinds.append("evicted")
        details.append(((pod.get("status") or {}).get("message") or "evicted").strip())

    for status in (pod.get("status") or {}).get("containerStatuses") or []:
        for state_key in ("state", "lastState"):
            terminated = (status.get(state_key) or {}).get("terminated") or {}
            if terminated.get("reason") == "OOMKilled":
                kinds.append("oomkilled")
                details.append(f"{status.get('name')} OOMKilled in {state_key}")
        terminated = (status.get("state") or {}).get("terminated") or {}
        exit_code = terminated.get("exitCode")
        if exit_code not in (None, 0) and terminated.get("reason") != "OOMKilled":
            kinds.append("nonzero_exit")
            details.append(f"{status.get('name')} exit {exit_code} ({terminated.get('reason')})")
        waiting_reason = ((status.get("state") or {}).get("waiting") or {}).get("reason")
        if waiting_reason in _WAITING_TROUBLE:
            kinds.append(_WAITING_TROUBLE[waiting_reason])
            details.append(f"{status.get('name')} {waiting_reason}")

    return tuple(dict.fromkeys(kinds)), "; ".join(details)


def get_pods(namespace: str, now: datetime.datetime | None = None) -> tuple[Pod, ...]:
    at = now or datetime.datetime.now(datetime.timezone.utc)
    raw = _kubectl_json(["get", "pods", "-n", namespace])
    pods = []
    for item in raw.get("items", []):
        status = item.get("status") or {}
        start = status.get("startTime")
        trouble, detail = _pod_trouble(item)
        pods.append(
            Pod(
                name=(item.get("metadata") or {}).get("name", "?"),
                node=(item.get("spec") or {}).get("nodeName") or "unscheduled",
                phase=status.get("phase", "?"),
                age_seconds=int((at - _parse_rfc3339(start)).total_seconds()) if start else 0,
                trouble=trouble,
                detail=detail,
            )
        )
    return tuple(pods)


def get_nodes() -> tuple[Node, ...]:
    raw = _kubectl_json(["get", "nodes"])
    return tuple(
        Node(
            name=(item.get("metadata") or {}).get("name", "?"),
            allocatable_memory_bytes=parse_quantity(
                ((item.get("status") or {}).get("allocatable") or {}).get("memory", "0")
            ),
            pressure=tuple(
                condition["type"]
                for condition in (item.get("status") or {}).get("conditions") or []
                if condition.get("type") in ("MemoryPressure", "DiskPressure")
                and condition.get("status") == "True"
            ),
        )
        for item in raw.get("items", [])
    )


def get_jobs(namespace: str) -> tuple[Job, ...]:
    raw = _kubectl_json(["get", "jobs", "-n", namespace])
    jobs = []
    for item in raw.get("items", []):
        status = item.get("status") or {}
        true_conditions = {
            condition.get("type")
            for condition in status.get("conditions") or []
            if condition.get("status") == "True"
        }
        state: JobState = (
            "complete"
            if "Complete" in true_conditions
            else "failed"
            if "Failed" in true_conditions
            else "active"
        )
        jobs.append(
            Job(
                name=(item.get("metadata") or {}).get("name", "?"),
                state=state,
                failed_pods=int(status.get("failed") or 0),
            )
        )
    return tuple(jobs)


def get_pod_memory(namespace: str, pods: ty.Sequence[Pod], nodes: ty.Sequence[Node]) -> MemoryStats | None:
    """None when metrics-server is unavailable, which is a normal degraded mode."""
    try:
        completed = subprocess.run(
            ["kubectl", "top", "pods", "-n", namespace, "--no-headers"],
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None

    node_allocatable = {node.name: node.allocatable_memory_bytes for node in nodes}
    pod_node = {pod.name: pod.node for pod in pods}

    measured = []
    for line in completed.stdout.splitlines():
        fields = line.split()
        if len(fields) < 3:
            continue
        node = pod_node.get(fields[0], "unscheduled")
        measured.append(
            PodMemory(
                pod=fields[0],
                node=node,
                used_bytes=parse_quantity(fields[2]),
                node_allocatable_bytes=node_allocatable.get(node, 0),
            )
        )
    if not measured:
        return None

    by_use = sorted(measured, key=lambda m: m.used_bytes)
    used = [m.used_bytes for m in by_use]
    return MemoryStats(
        samples=len(used),
        p50_bytes=used[min(len(used) // 2, len(used) - 1)],
        p90_bytes=used[min(int(len(used) * 0.9), len(used) - 1)],
        max_bytes=used[-1],
        mean_bytes=sum(used) // len(used),
        worst=max(measured, key=lambda m: m.pct_of_node),
    )


class LocalProcess(ty.NamedTuple):
    """An orchestrator running on this machine."""

    pid: int

    def describe(self) -> str:
        return f"pid {self.pid}"

    def alive(self) -> bool:
        return process_alive(self.pid)

    def elapsed(self) -> str:
        return process_elapsed(self.pid)


class PodProcess(ty.NamedTuple):
    """An orchestrator running inside a pod, reached through `kubectl exec`. The pod is a
    bare pod (not a Job), so deleting a namespace's Jobs leaves it standing."""

    pod: str
    namespace: str
    pid: int

    def describe(self) -> str:
        return f"pod {self.pod} pid {self.pid}"

    def alive(self) -> bool:
        """False once the process has exited or the pod is gone. A kubectl failure for any
        other reason (timeout, auth, API outage) raises ProbeError rather than reporting a
        death that was not observed."""
        completed = _exec_in_pod(self.pod, self.namespace, ["sh", "-c", f"kill -0 {self.pid}"])
        if completed.returncode == 0:
            return True
        if _pod_is_gone(completed.stderr) or "No such process" in completed.stderr:
            return False
        if completed.returncode == 1 and not completed.stderr.strip():
            return False
        raise ProbeError(
            f"kubectl exec {self.pod} failed ({completed.returncode}): {completed.stderr.strip()}"
        )

    def elapsed(self) -> str:
        completed = _exec_in_pod(self.pod, self.namespace, ["ps", "-o", "etime=", "-p", str(self.pid)])
        return completed.stdout.strip() or "unknown"


Orchestrator = LocalProcess | PodProcess

_POD_GONE_MARKERS = ("NotFound", "not found", "is not running", "container not found")


def _pod_is_gone(stderr: str) -> bool:
    return any(marker in stderr for marker in _POD_GONE_MARKERS)


def _exec_in_pod(
    pod: str, namespace: str, command: ty.Sequence[str], timeout: int = 30
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["kubectl", "exec", pod, "-n", namespace, "--", *command],
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        raise ProbeError(f"kubectl exec {pod} failed: {exc}") from exc


def oldest_matching_pid(ps_output: str, pattern: str) -> int | None:
    """From `ps -eo pid=,etimes=,args=` output, the pid of the longest-running process whose
    command line matches `pattern`; None when nothing matches."""
    matches = []
    for line in ps_output.splitlines():
        fields = line.split(None, 2)
        if len(fields) < 3:
            continue
        pid, elapsed_seconds, args = fields
        if re.search(pattern, args):
            matches.append((int(elapsed_seconds), int(pid)))
    if not matches:
        return None
    _, pid_of_oldest = max(matches)
    return pid_of_oldest


def find_pod_process(pod: str, namespace: str, pattern: str) -> int:
    """The pid of the oldest process in the pod whose command line matches `pattern`."""
    completed = _exec_in_pod(pod, namespace, ["ps", "-eo", "pid=,etimes=,args="])
    if completed.returncode != 0:
        raise ProbeError(f"ps in {pod} failed ({completed.returncode}): {completed.stderr.strip()}")
    pid = oldest_matching_pid(completed.stdout, pattern)
    if pid is None:
        raise ProbeError(f"no process in {pod} matches /{pattern}/")
    return pid


DEFAULT_POD_PROCESS_PATTERN = r"python[0-9.]* .*run\.py"


def add_orchestrator_args(parser: argparse.ArgumentParser) -> None:
    """`--pid` for a local orchestrator, or `--pod` for one inside a pod in `--namespace`."""
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--pid", type=int, help="local orchestrator pid")
    target.add_argument("--pod", help="pod running the orchestrator, in --namespace")
    parser.add_argument(
        "--pod-pid",
        type=int,
        help="the orchestrator's pid inside --pod; found by --pod-pattern when omitted",
    )
    parser.add_argument(
        "--pod-pattern",
        default=DEFAULT_POD_PROCESS_PATTERN,
        help="regex over a command line in --pod that picks the orchestrator process (oldest match wins)",
    )
    parser.add_argument("--namespace", default="caleb-gregory")


def orchestrator_from_args(args: argparse.Namespace) -> Orchestrator:
    if args.pid is not None:
        return LocalProcess(args.pid)
    pid = (
        args.pod_pid
        if args.pod_pid is not None
        else find_pod_process(args.pod, args.namespace, args.pod_pattern)
    )
    return PodProcess(args.pod, args.namespace, pid)


def process_alive(pid: int) -> bool:
    import os

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def process_elapsed(pid: int) -> str:
    try:
        completed = subprocess.run(
            ["ps", "-p", str(pid), "-o", "etime="],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown"
    return completed.stdout.strip() or "unknown"
