#!/usr/bin/env python3
"""Kill switch for an overnight mops pipeline: poll a namespace for OOMKilled pods;
once the number of distinct OOMKilled containers seen reaches --kill-after (default 1),
SIGTERM the local orchestrator process and delete all Jobs in the namespace so nothing
keeps burning spot nodes.

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


def _process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


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
    parser.add_argument(
        "--pid", type=int, required=True, help="local orchestrator pid to SIGTERM on trigger"
    )
    parser.add_argument("--namespace", default="caleb-gregory")
    parser.add_argument("--interval", type=int, default=60, help="poll interval seconds")
    parser.add_argument(
        "--kill-after",
        type=int,
        default=1,
        help="number of distinct OOMKilled containers that triggers the kill",
    )
    args = parser.parse_args()

    _log(
        f"watching namespace={args.namespace} every {args.interval}s; "
        f"after {args.kill_after} distinct OOMKilled container(s) will SIGTERM pid {args.pid} "
        f"then delete all jobs"
    )
    consecutive_errors = 0
    polls = 0
    seen_oom: dict[str, str] = {}
    while True:
        if not _process_alive(args.pid):
            _log(f"orchestrator pid {args.pid} has exited; nothing left to watch — exiting")
            sys.exit(0)
        try:
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
            _kill_local_process(args.pid)
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
