#!/usr/bin/env python3
"""Kill switch for an overnight mops pipeline: poll a namespace for OOMKilled pods;
once the number of distinct OOMKilled containers seen reaches --kill-after (default 1),
SIGTERM the orchestrator process (local with --pid, or inside a pod with --pod) and delete
all Jobs in the namespace so nothing keeps burning spot nodes. An orchestrator pod is a
bare pod, not a Job, so the delete leaves it standing for a post-mortem.

The count accumulates across polls, so pods that Kubernetes garbage-collects between
polls still count once observed.

Stdlib-only; run with any python3. Ctrl-C to stop it without triggering.
"""

import argparse
import datetime
import json
import os
import signal
import subprocess
import sys
import time

from tools.k8s import _probe


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _log(msg: str) -> None:
    print(f"[{_now()}] {msg}", flush=True)


def _get_pods(namespace: str) -> dict:
    out = subprocess.run(
        ["kubectl", "get", "pods", "-n", namespace, "-o", "json"],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return dict(json.loads(out.stdout))


def _find_oomkilled(pods: dict) -> dict[str, str]:
    """Map each OOMKilled container (`pod/container`) to a one-line description."""
    return {
        f"{pod['metadata']['name']}/{cs['name']}": (
            f"{pod['metadata']['name']}/{cs['name']} ({state_key}, exit {term.get('exitCode')})"
        )
        for pod in pods.get("items", [])
        for cs in (pod.get("status", {}).get("containerStatuses") or [])
        for state_key in ("state", "lastState")
        for term in [(cs.get(state_key) or {}).get("terminated") or {}]
        if term.get("reason") == "OOMKilled"
    }


def _kill_pod_process(orchestrator: _probe.PodProcess, grace_seconds: int = 15) -> None:
    pod, namespace, pid = orchestrator
    _log(f"DESTRUCTIVE: sending SIGTERM to orchestrator pid {pid} in pod {pod}")
    subprocess.run(
        ["kubectl", "exec", pod, "-n", namespace, "--", "sh", "-c", f"kill -TERM {pid}"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    deadline = time.time() + grace_seconds
    while time.time() < deadline:
        try:
            if not orchestrator.alive():
                _log(f"pid {pid} in pod {pod} exited after SIGTERM")
                return
        except _probe.ProbeError as exc:
            _log(f"WARN: could not confirm the exit: {exc}")
        time.sleep(1)
    _log(f"DESTRUCTIVE: pid {pid} in pod {pod} still alive after {grace_seconds}s; sending SIGKILL")
    subprocess.run(
        ["kubectl", "exec", pod, "-n", namespace, "--", "sh", "-c", f"kill -KILL {pid}"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def _kill_orchestrator(orchestrator: _probe.Orchestrator) -> None:
    if isinstance(orchestrator, _probe.PodProcess):
        _kill_pod_process(orchestrator)
    else:
        _kill_local_process(orchestrator.pid)


def _kill_local_process(pid: int, grace_seconds: int = 15) -> None:
    _log(f"DESTRUCTIVE: sending SIGTERM to local orchestrator pid {pid}")
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        _log(f"pid {pid} already gone")
        return
    deadline = time.time() + grace_seconds
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            _log(f"pid {pid} exited after SIGTERM")
            return
        time.sleep(1)
    _log(f"DESTRUCTIVE: pid {pid} still alive after {grace_seconds}s; sending SIGKILL")
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _delete_all_jobs(namespace: str) -> None:
    _log(f"DESTRUCTIVE: deleting ALL jobs in namespace {namespace}")
    result = subprocess.run(
        ["kubectl", "delete", "jobs", "--namespace", namespace, "--all", "--wait=false"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    _log(f"kubectl delete jobs exited {result.returncode}")
    if result.stdout.strip():
        _log(result.stdout.strip()[-2000:])
    if result.stderr.strip():
        _log(f"stderr: {result.stderr.strip()[-2000:]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    _probe.add_orchestrator_args(parser)
    parser.add_argument("--interval", type=int, default=60, help="poll interval seconds")
    parser.add_argument(
        "--kill-after",
        type=int,
        default=1,
        help="number of distinct OOMKilled containers that triggers the kill",
    )
    args = parser.parse_args()
    try:
        orchestrator = _probe.orchestrator_from_args(args)
    except _probe.ProbeError as exc:
        _log(f"cannot find the orchestrator: {exc}")
        sys.exit(2)

    _log(
        f"watching namespace={args.namespace} every {args.interval}s; "
        f"after {args.kill_after} distinct OOMKilled container(s) will SIGTERM "
        f"{orchestrator.describe()} then delete all jobs"
    )
    consecutive_errors = 0
    polls = 0
    seen_oom: dict[str, str] = {}
    while True:
        try:
            if not orchestrator.alive():
                _log(f"orchestrator {orchestrator.describe()} has exited; nothing left to watch — exiting")
                sys.exit(0)
            pods = _get_pods(args.namespace)
            consecutive_errors = 0
        except Exception as e:
            consecutive_errors += 1
            _log(f"WARN: poll failed ({consecutive_errors} in a row): {e}")
            time.sleep(min(args.interval * consecutive_errors, 300))
            continue

        new_oom = {k: v for k, v in _find_oomkilled(pods).items() if k not in seen_oom}
        if new_oom:
            seen_oom.update(new_oom)
            _log(
                f"OOMKilled detected in {len(new_oom)} new container(s) "
                f"({len(seen_oom)}/{args.kill_after} toward kill):"
            )
            for hit in new_oom.values():
                _log(f"  {hit}")
        if len(seen_oom) >= args.kill_after:
            _kill_orchestrator(orchestrator)
            _delete_all_jobs(args.namespace)
            _log("done; exiting")
            sys.exit(1)

        polls += 1
        if polls % 20 == 0:
            n = len(pods.get("items", []))
            _log(f"heartbeat: {n} pods, {len(seen_oom)}/{args.kill_after} OOMKilled so far")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
