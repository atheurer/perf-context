---
id: cgroup-cpu-throttling
title: "cgroup v2 CPU bandwidth throttling: detection and diagnosis"
type: concept
domain: kernel
tags: [cgroup-throttled, high-sys-cpu, low-cpu-low-throughput]
source_id: kernel-docs
source_url: https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html
source_license: GPL-2.0
license_verified: false
track: core
applicability:
  kernel: ">=4.15 (cgroup v2 CPU controller stable); RHEL9+ default cgroup v2"
  hardware: any
  software: containerized workloads; Kubernetes pods with CPU limits
tokens:
  abstract: 49
  digest: 490
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# cgroup v2 CPU bandwidth throttling: detection and diagnosis

## Abstract
The cgroup v2 CPU bandwidth controller throttles processes that exceed their
`cpu.max` quota within a period. A throttled process is put to sleep until the
next period, causing latency spikes and throughput degradation while the host
CPU may appear idle. The symptom is an application running slowly with low
per-host CPU utilization — the missing signal is `nr_throttled` in `cpu.stat`.

## Digest
**Mechanism.** `cpu.max` defines `quota period` in microseconds. A cgroup may
use at most `quota` µs of CPU time within each `period` µs window (default
period: 100ms). When quota is exhausted mid-period, all threads in the cgroup
are throttled (sleeping) until the next period starts. With a 100ms period,
throttling causes discrete 0–100ms latency injections — enough to make p99
latency spike while p50 looks fine.

**Detection:**
```bash
# Find the cgroup for a running process
cat /proc/<pid>/cgroup

# Read throttle stats (cgroup v2)
cat /sys/fs/cgroup/<path>/cpu.stat
# Fields:
#   nr_periods      — total scheduling periods elapsed
#   nr_throttled    — periods where the cgroup was throttled (at least partially)
#   throttled_usec  — total microseconds throttled

# Quick check: if nr_throttled > 0 and growing, throttling is active
watch -n 1 'cat /sys/fs/cgroup/<path>/cpu.stat | grep throttled'
```
Any non-zero and growing `nr_throttled` on a latency-sensitive workload is
worth investigating, even if the throttle fraction is small.

**The "1000 CPUs, 0.1 CPU limit" failure mode.** A container in Kubernetes
given `requests: 100m` (0.1 CPU) but no `limits` gets scheduled on a 64-core
host and may see no throttling. But `limits: 100m` gives it exactly 10ms per
100ms period — 10% of one CPU, regardless of host idle capacity. If the
workload naturally uses 0.5 CPUs for 20ms then is idle, it will throttle every
other period. Kubernetes CPU limits cause more throttling than their numeric
value implies because real workloads have bursty CPU usage, not uniform usage.

**PSI as a corroborating signal:**
```bash
cat /sys/fs/cgroup/<path>/cpu.pressure
# avg10, avg60, avg300 > 5% sustained indicates meaningful CPU stall time
```

**Read `cpu.max`:**
```bash
cat /sys/fs/cgroup/<path>/cpu.max
# "max 100000" → unlimited (no quota)
# "10000 100000" → 10ms/100ms = 10% of one CPU = 100 millicores
```

**RHEL9 vs RHEL10 context.** RHEL9 moved to cgroup v2 by default. If a
benchmark compares a RHEL9 host with cgroup v1 to RHEL10 with cgroup v2, the
CPU accounting and throttling semantics differ. On bare-metal benchmarks without
containers this is irrelevant; in containerized setups it is a variable to
control. Verify `cat /proc/mounts | grep cgroup`.

**Remediation.** Increase quota or remove the limit. In Kubernetes: raise
`resources.limits.cpu` or remove it if the workload should be best-effort.
For burst-tolerant workloads, consider `cpu.max.burst` (cgroup v2, kernel >=5.14)
which allows quota accumulation across idle periods.

## Pointers
- Kernel doc: `Documentation/admin-guide/cgroup-v2.rst` (cpu controller section)
- LWN "Fixing bandwidth throttling": https://lwn.net/Articles/844976/
- Related units: `psi-pressure-stall`, `rhel9-rhel10-kernel-delta`
- Annex raw: none
