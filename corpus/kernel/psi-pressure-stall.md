---
id: psi-pressure-stall
title: "Pressure Stall Information (PSI): reading CPU/memory/IO pressure metrics"
type: tool
domain: kernel
tags: [cgroup-throttled, memory-pressure, iowait-high, throughput-collapse]
source_id: kernel-docs
source_url: https://www.kernel.org/doc/html/latest/accounting/psi.html
source_license: GPL-2.0
license_verified: false
track: core
applicability:
  kernel: ">=4.20 (PSI merged); RHEL9+ available; per-cgroup PSI: >=5.2"
  hardware: any
  software: any
tokens:
  abstract: 47
  digest: 460
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# Pressure Stall Information (PSI): reading CPU/memory/IO pressure metrics

## Abstract
PSI measures the fraction of time tasks spent stalled waiting for CPU, memory,
or I/O resources. Unlike utilization (which measures busy time), PSI measures
demand-exceeds-supply time — a system can be 60% CPU utilized with 0% PSI, or
30% PSI. Per-cgroup PSI is the right tool for diagnosing container CPU or
memory throttling without relying on coarse cgroup stat counters alone.

## Digest
**Reading system-wide PSI:**
```bash
cat /proc/pressure/cpu
# some avg10=0.52 avg60=0.38 avg300=0.21 total=1234567

cat /proc/pressure/memory
# some avg10=0.00 avg60=0.02 avg300=0.00 total=0
# full avg10=0.00 avg60=0.00 avg300=0.00 total=0

cat /proc/pressure/io
# some avg10=1.24 avg60=0.89 avg300=0.43 total=456789
```

**Field semantics:**
- `some` — fraction of time at least one task was stalled waiting for this
  resource. Indicates the resource is sometimes a bottleneck.
- `full` — fraction of time *all* runnable tasks were stalled (CPU idle or
  all blocked). `full > 0` for CPU means CPUs went idle not by choice but
  because all tasks were blocked — usually I/O or memory stall causing CPU
  underutilization.
- `avg10/avg60/avg300` — exponential moving averages over 10s, 60s, 300s.
  `avg10 > 5%` for memory `full` is a meaningful signal of memory pressure.
  `avg10 > 20%` for IO `some` indicates sustained I/O bottleneck.

**Per-cgroup PSI (cgroup v2):**
```bash
cat /sys/fs/cgroup/<path>/cpu.pressure
cat /sys/fs/cgroup/<path>/memory.pressure
cat /sys/fs/cgroup/<path>/io.pressure
```
Same format as system-wide. A container showing `cpu.pressure some avg10 > 10%`
while the host CPU is idle is the signature of CPU quota throttling (see
`cgroup-cpu-throttling`).

**PSI vs utilization.** A benchmark host showing 50% CPU utilization with
`/proc/pressure/cpu some avg60 = 8%` has tasks waiting 8% of the time even
though CPUs appear half-idle. This means some CPUs are busy and others have
tasks waiting — a scheduling imbalance. PSI catches this; utilization averages
hide it.

**PSI vs iowait.** `%iowait` in mpstat measures idle CPU time while a task
waits on I/O (CPU-centric view). `io.pressure some` measures task stall time
waiting for I/O (task-centric view). They can diverge: high iowait with low
io.pressure means the waiting task has no peers competing for CPU. High
io.pressure with low iowait means many tasks are I/O-blocked but other tasks
keep CPUs busy.

**Monitoring during benchmark runs:**
```bash
# Watch PSI during uperf
watch -n 1 'cat /proc/pressure/{cpu,memory,io}'

# Or log periodically
while true; do
  echo "$(date) CPU: $(cat /proc/pressure/cpu)"
  sleep 5
done > psi_log.txt
```

**Alerting thresholds** [distiller-added, based on PSI documentation guidance]:
- memory `full avg60 > 0.1%` → investigate memory reclaim pressure
- cpu `some avg60 > 15%` → meaningful CPU stall, check cgroup limits or scheduling
- io `some avg60 > 5%` → sustained I/O waiting

## Pointers
- LWN "PSI — Pressure Stall Information": https://lwn.net/Articles/759781/
- Kernel doc: `Documentation/accounting/psi.rst`
- Related units: `cgroup-cpu-throttling`, `cgroup-memory-high-reclaim`, `mpstat-sar-cpu-breakdown`
- Annex raw: none
