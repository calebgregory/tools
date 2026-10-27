---
name: monitor-k8s-run
description: Babysit a long-running Kubernetes pipeline driven by a local orchestrator process, using the k8s run-monitoring scripts in ~/tools/main. Invoke with /monitor-k8s-run <orchestrator-pid> [namespace].
---

Watch a mops-style run - one local orchestrator process submitting many Jobs into one
namespace - and report on its health until it finishes. Kill the run only on an observed
OOMKilled, never on a prediction.

## Inputs

- **orchestrator** (required), one of:
  - `--pid <pid>`: a local orchestrator process. The user normally supplies it. If not, find
    it with `ps -ef | grep -i <pipeline-name>` and confirm the match with the user before
    arming anything, since the pid becomes a kill target.
  - `--pod <pod>`: an orchestrator running inside a pod in the namespace (the katamari
    README's "From an orchestrator pod" flow). The tools find the run's process with
    `ps` over `kubectl exec`, matching `--pod-pattern` (default: a python process running a
    `run.py`) and taking the oldest match; `--pod-pid` names it directly. Liveness and the
    kill go through `kubectl exec` too.
- **namespace** (default `caleb-gregory`). With `--pod`, also the pod's namespace.

Confirm the orchestrator is alive and note what it is running before starting. Locally,
`ps -p <pid> -o pid,etime,command`; in a pod,
`kubectl exec <pod> -n <ns> -- ps -eo pid,etime,args`.

A pod started by `libs/mops/k8s-pod/connect.py` runs `thds.core.exit_after` as pid 1 with
the `--shutdown-hours` budget, so the pod, and the run in it, die when that budget is
spent. Read the budget from pid 1's command line and compare it with the expected run
length up front. Its tmux session is `debug`; `kubectl exec -it <pod> -n <ns> -- tmux
attach -t debug` joins it, and `tmux capture-pane -p -t debug` over `kubectl exec` reads
the run's own output without attaching. The orchestrator pod is a bare pod, not a Job, so
the watchdog's job delete leaves it standing.

## Tools

Three commands, installed globally from `~/tools/main` via `uv tool install -e .`. Source
lives in `src/tools/k8s/`.

| Command | Role |
|---|---|
| `k8s-oom-watchdog` | **Kill switch.** On OOMKilled: SIGTERM the pid, then delete all Jobs. |
| `k8s-run-watch` | Event stream for the Monitor tool. Reports; never kills. |
| `k8s-run-status` | One-shot snapshot for triage. |

All three take `--pid` or `--pod`, and `--namespace`. Below, `<target>` stands for
whichever you have: `--pid <pid>` or `--pod <pod>`. If a command is not found, the tool
needs reinstalling: `cd ~/tools/main && uv tool install -e .`.

## Setup

Run these three steps at the start, in order.

**1. Baseline.** Capture the starting state so later changes are interpretable:

```bash
k8s-run-status <target> --namespace <ns>
```

**2. Arm the kill switch** as a background Bash task (not Monitor - it needs no
notifications, and it exits on its own):

```bash
k8s-oom-watchdog <target> --namespace <ns> --interval 60
```

**3. Arm observation** with the Monitor tool, `persistent: true`:

```bash
k8s-run-watch <target> --namespace <ns>
```

Both watchers exit by themselves when the orchestrator process disappears, so there is
nothing to clean up afterward. With `--pod`, a transient `kubectl exec` failure is reported
as a probe error and retried, never read as the orchestrator dying.

Tell the user which watcher holds kill authority and which only reports. They need to know
that a silent watchdog is not the same as a healthy run.

## Rules of engagement

**An OOMKilled container is the kill signal. A projection is not.** Do not SIGTERM the
orchestrator because memory is trending toward node capacity. A trend fitted to two or
three samples is a guess, memory that looks like it is marching at the wall usually
plateaus when the workload flushes, and killing on the guess throws away hours of finished
work to prevent a failure that may never happen. Report the trend, name the headroom, say
what you expect - then leave it alone.

**Only `k8s-oom-watchdog` kills during a run.** Predictive monitoring is information.

**Evictions are reported, not acted on.** Kubernetes Jobs retry them (`backoffLimit` is
typically 6), so evictions are usually self-healing. Say how many, on which nodes, and
whether replacements are running.

**Cleanup is authorized in one case:** the orchestrator has died and left pods still
Running or Pending. Nothing will ever collect them, so they would spin indefinitely. Then
delete the Jobs in the namespace. Confirm the orchestrator is genuinely gone first
(`ps -p <pid>` locally; `k8s-run-status --pod <pod>` says GONE for a pod), and say what you
deleted.

## Reading the signals correctly

These are the misreadings that waste time or trigger a wrong kill.

**Zero completions is not a stall.** Individual jobs can run an hour. Get the unit cost
from the first job that finishes (`.status.startTime` to `.status.completionTime`), then
expect the rest to land in a wave, because they all started together. Judge a stall by
whether pods are progressing in their logs, not by the completion count.

**Falling job and pod counts are normal.** Kubernetes garbage-collects finished Jobs on
their TTL, so `Complete` can drop from 483 to 3 with nothing lost. Never report a falling
count as lost work. `k8s-run-status` says so in its output for this reason.

**Memory sawtooths.** Batch workloads allocate then flush, so the fleet average rises and
falls while the max stays flat. Ramp-up samples, taken while pods are still filling their
working set, overstate growth badly - a rate measured there can be ten times the
steady-state rate. Before calling any trend, collect more than three samples over at least
ten minutes: `k8s-run-watch --interval 60 --heartbeat-polls 1` turns the heartbeat into a
sampling line for exactly this.

**Trust `kubectl top`, not the application's own memory report.** A `thds.core.journalist`
line (`MEM cur 234.5 / 235.2 peak GB`) can sit tens of GB above the cgroup number for the
same pod, because it counts things the kubelet does not. Do eviction math on `kubectl top`,
which is closer to what the kubelet acts on.

**Cumulative bytes written is not disk in use.** A log reporting `total GB 227.6w` says
nothing about resident disk. Check the node:
`kubectl get --raw "/api/v1/nodes/<node>/proxy/stats/summary" | jq .node.fs`.

**Group failures by node before blaming the workload.** If every eviction sits on one node,
it is that node. Check `DiskPressure` and `MemoryPressure` conditions across the pool;
Kubernetes taints a sick node and the pool sheds it. `k8s-run-status` calls this out.

**Requests without limits change how failure looks.** A pod with memory `requests` and no
`limits` is Burstable QoS, so exhausting the node shows up as a kubelet eviction rather
than an OOMKilled container - and `k8s-oom-watchdog` will not fire. Check with
`kubectl get pod <pod> -o jsonpath='{.spec.containers[0].resources}'` and tell the user, so
watchdog silence is not mistaken for a guarantee.

**Watch the units.** `202,114Mi` is 197.4Gi, not 202Gi. Let `_probe.format_gib` do the
conversion instead of eyeballing it.

## While the run is going

Answer each Monitor event by deciding whether it changes anything, then say so briefly.

- **Routine heartbeat**: one or two sentences. Do not re-derive the whole picture.
- **New trouble**: run `k8s-run-status`, group by node, check whether replacements are
  running, and pull logs from an affected pod (`kubectl logs <pod> --tail=25`).
- **Memory or pressure warning**: report the headroom and the trend. Do not act.

Never invent an event that has not arrived, and never treat a background notification as
the user approving something.

## When the orchestrator exits

Determine whether it finished or died, and say which. The evidence is cluster-side:

```bash
k8s-run-status <target> --namespace <ns>
```

A clean finish shows every job `complete`, nothing Running or Pending, and no pod with a
nonzero exit. A crash leaves jobs stranded in `active` with pods still Running - that is
the orphan case, where deleting the Jobs is authorized.

Report, in this order: whether it succeeded, how long it took, what failed and whether it
self-healed, and anything you flagged that turned out to be a non-issue. Say plainly when a
concern you raised was unfounded. Then note what you cannot see from the cluster: the
orchestrator's own exit code and final output went to the user's terminal (or, for a pod,
its tmux pane: `kubectl exec <pod> -n <ns> -- tmux capture-pane -p -t debug -S -200`, as
long as the pod is still up), and the pipeline's output data needs its own check.
