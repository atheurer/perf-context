---
id: pidstat-context-switches
title: "pidstat: per-process context switches, CPU usage, and thread diagnosis"
type: tool
domain: observability
tags: [high-sys-cpu, lock-contention, run-queue-long, low-cpu-low-throughput]
source_id: sysstat
source_url: https://github.com/sysstat/sysstat
source_license: GPL-2.0
license_verified: false
track: core
applicability:
  kernel: any
  hardware: any
  software: any
tokens:
  abstract: 43
  digest: 460
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# pidstat: per-process context switches, CPU usage, and thread diagnosis

## Abstract
`pidstat -w` shows voluntary and involuntary context switch rates per process.
The split between voluntary (task blocked and released CPU) and involuntary
(scheduler preempted task) is a direct diagnostic signal: high voluntary
indicates blocking (I/O, locks); high involuntary indicates scheduling pressure
or a scheduler behavior change like the CFS→EEVDF transition between RHEL9
and RHEL10.

## Digest
**Core command:**
```bash
pidstat -w 1 30       # context switches per second, all processes, 30 samples
pidstat -w -t 1 30    # include per-thread breakdown (-t)
pidstat -w -p <pid> 1 30   # specific process only
```
Output columns: `cswch/s` (voluntary) and `nvcswch/s` (involuntary).

**Interpretation:**

*High voluntary `cswch/s`* — the process is frequently blocking and releasing
the CPU willingly. Causes: waiting for I/O, network socket read, mutex
acquisition, condition variable wait, or `sched_yield`. For a network benchmark
like uperf, moderate voluntary switches are expected (receiver blocks on
`recv()`). Abnormally high voluntary switches (>10k/s for a single-threaded
process) suggest lock contention — use off-CPU analysis to confirm.

*High involuntary `nvcswch/s`* — the scheduler is preempting the process before
it voluntarily yields. Causes: time-slice expiry (the default 4–8ms CFS slice),
higher-priority task wakeup, or scheduler configuration. EEVDF (RHEL10) changes
preemption timing vs CFS (RHEL9): the same workload may show different
`nvcswch/s` between the two releases. This is not inherently bad — EEVDF
preempts to enforce deadlines which improves fairness — but the rate change is
a scheduler attribution signal.

**Comparing RHEL9 vs RHEL10:**
```bash
# Run on both hosts simultaneously during the benchmark
pidstat -w -t -p <uperf_pid> 1 > cswitch_rhel9.txt
pidstat -w -t -p <uperf_pid> 1 > cswitch_rhel10.txt
```
If RHEL10 shows significantly higher `nvcswch/s` at the same load: EEVDF is
preempting more aggressively. Check whether throughput also improved (more
preemption can mean better fairness and higher aggregate throughput) or degraded
(preemption overhead exceeds benefit for this workload).

**Rule of thumb magnitudes** [distiller-added from general knowledge]:
- < 1000 cswch/s for a busy single-threaded process: normal
- 5000–20000 cswch/s: elevated, worth investigating
- > 50000 cswch/s: almost certainly a problem (lock storm, thrashing)
- nvcswch/s > cswch/s: more preemptions than voluntary yields — unusual for
  I/O-bound work, normal for CPU-bound multi-threaded work

**Combined with CPU usage:**
```bash
pidstat -u -w 1 30    # CPU% + context switches together
```
A process with high `%CPU` and high `nvcswch/s` is CPU-saturated and being
preempted repeatedly. A process with low `%CPU` and high `cswch/s` is
I/O-blocked or lock-contended.

## Pointers
- `man pidstat`
- Related units: `eevdf-vs-cfs`, `mpstat-sar-cpu-breakdown`, `off-cpu-analysis`
- Annex raw: none
