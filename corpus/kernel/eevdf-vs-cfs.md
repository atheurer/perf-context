---
id: eevdf-vs-cfs
title: "EEVDF scheduler vs CFS: behavior, RHEL version split, and diagnostic signals"
type: concept
domain: kernel
tags: [high-sys-cpu, run-queue-long, low-cpu-low-throughput, p99-tail]
source_id: lwn
source_url: https://lwn.net/Articles/925371/
source_license: all-rights-reserved
license_verified: false
track: digest
applicability:
  kernel: "upstream >=6.6 (EEVDF merged 2023-09-10); RHEL10 (kernel-6.12-based): yes; RHEL9 (kernel-5.14-based): CFS only — EEVDF not backported; verify: `uname -r` and `cat /sys/kernel/debug/sched/features 2>/dev/null | grep -i eevdf`"
  hardware: x86_64
  software: any
tokens:
  abstract: 52
  digest: 570
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# EEVDF scheduler vs CFS: behavior, RHEL version split, and diagnostic signals

## Abstract
EEVDF (Earliest Eligible Virtual Deadline First) replaced CFS as the Linux
default scheduler in kernel 6.6. RHEL10 (kernel-6.12-based) runs EEVDF; RHEL9
(kernel-5.14-based) runs CFS. When comparing the two OS releases, scheduler
behavior differences — especially wakeup latency and preemption patterns — are
a first-order explanation to test before attributing differences to hardware or
network changes.

## Digest
**Mechanism difference.** CFS schedules by minimizing `vruntime` (weighted
virtual runtime) — the task with smallest vruntime runs next. Fairness is
enforced globally but the scheduler has no deadline concept: a woken task may
wait arbitrarily if many runnable tasks exist. EEVDF adds a *virtual deadline*
to each task (based on slice length and lag) and requires a task to be
*eligible* (virtual start time ≤ current virtual time) before it can be
scheduled. The net effect: tasks that have been waiting longer, or that are
running at lighter-than-fair rates, are promoted faster. Latency-sensitive
tasks that sleep and wake frequently tend to see more consistent wakeup times
under EEVDF. [distiller-added: the detailed lag/virtual-deadline math is in
`Documentation/scheduler/sched-eevdf.rst`.]

**Behavioral differences to expect** when moving from RHEL9 (CFS) to RHEL10
(EEVDF):
- *Wakeup latency distribution tightens* for mixed workloads — tasks waiting
  in run-queue stall less. This can appear as lower p99 at the same load, or
  as improved throughput on wake-heavy workloads (uperf stream at low thread
  counts falls here).
- *Involuntary context switch rate changes.* EEVDF preempts based on deadline
  expiry rather than vruntime overtake; the rate and distribution of preemptions
  differ. Measure with `pidstat -w 1` — a meaningful involuntary cswch/s
  change between RHEL9 and RHEL10 is a scheduler signal.
- *Run-queue depth distribution shifts.* Under CFS, tasks pile up waiting for
  vruntime to converge; EEVDF drains the run queue more evenly. Check
  `sar -q 1` (runq-sz column) or `/proc/schedstat` between the two runs.
- *Some workloads regress.* Early EEVDF (6.6) had regressions on
  highly-threaded CPU-bound workloads; most were fixed by 6.8–6.10. RHEL10's
  6.12-based kernel should have the stable version, but verify with the
  specific workload.

**Discriminating measurements** (apply to both runs, then diff):
```
# Context switch rate per process
pidstat -w 1 30

# Run-queue depth over time
sar -q 1 30

# Scheduler wakeup latency distribution (expensive — short trace)
perf sched record -- sleep 5
perf sched latency --sort max

# Verify which scheduler is active
cat /sys/kernel/debug/sched/features   # EEVDF appears if active
```

**RHEL backport caveat.** EEVDF is not backported to RHEL9. A host reporting
`5.14.0-*` in `uname -r` is running CFS regardless of upstream version. On
RHEL10, `6.12.0-*` implies EEVDF is default; confirm with `sched/features`.

**Misinterpretation trap.** Higher involuntary context switches on RHEL10 vs
RHEL9 does *not* mean RHEL10 is slower — EEVDF preempts more to enforce
deadlines, which improves fairness but adds switch overhead. Whether the net
effect is positive or negative depends on the workload; always look at the
throughput and latency numbers alongside the switch rate, not the switch rate
alone.

## Pointers
- LWN "An EEVDF CPU scheduler for Linux": https://lwn.net/Articles/925371/
- Kernel doc: `Documentation/scheduler/sched-eevdf.rst` (upstream 6.6+)
- Related units: `rhel9-rhel10-kernel-delta`, `perf-sched-timehist`, `pidstat-context-switches`
- Annex raw: none
