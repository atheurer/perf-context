---
id: perf-stat-record
title: "perf stat and perf record: PMU counter measurement and CPU profiling"
type: tool
domain: observability
tags: [low-ipc, high-sys-cpu, high-user-cpu, frontend-bound, backend-bound]
source_id: perf-wiki
source_url: https://perf.wiki.kernel.org/index.php/Tutorial
source_license: GPL-2.0
license_verified: false
track: core
applicability:
  kernel: ">=4.x (modern perf); requires perf_event_paranoid <=1 or CAP_PERFMON"
  hardware: x86_64 Intel/AMD; aarch64 Neoverse
  software: any
tokens:
  abstract: 42
  digest: 490
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# perf stat and perf record: PMU counter measurement and CPU profiling

## Abstract
`perf stat` measures hardware performance counters for a workload — cycles,
instructions, IPC, cache misses, and context switches — giving a system-wide
or per-process profile in seconds. IPC below ~0.5 indicates memory-bound
execution; above 3 indicates well-optimized compute. It is the fastest
first-pass tool for distinguishing compute-bound, memory-bound, and
scheduler-overhead workloads.

## Digest
**System-wide baseline (30 second window):**
```bash
perf stat -a -e cycles,instructions,cache-misses,cache-references,\
context-switches,page-faults,branch-misses sleep 30
```
Key output ratios:
- `instructions / cycles` = IPC. <0.5 → memory-bound; 1–2 → typical compute;
  >3 → well-vectorized or highly pipelined.
- `cache-misses / cache-references` = LLC miss rate. >5% is high for most
  workloads.
- `branch-misses / branches` = branch misprediction rate. >2% warrants
  investigation.

**Per-process stat:**
```bash
perf stat -p <pid> sleep 10
# or attach to a running command:
perf stat -- uperf -m stream -t 1 -l 30 ...
```

**Context switch and page fault counters** from `perf stat` match `pidstat`
but are more precise for short windows. Use when `pidstat`'s 1-second
granularity is too coarse.

**Syscall rate:**
```bash
perf stat -e 'syscalls:sys_enter_*' -a sleep 10 2>&1 | grep -v " 0 " | sort -rn
```
This reveals which syscalls dominate — relevant for attributing `%sys` CPU
overhead to mitigation cost vs scheduler overhead.

**Sampling with perf record:**
```bash
# CPU flame graph data
perf record -F 99 -a -g -- sleep 30
perf script | stackcollapse-perf.pl | flamegraph.pl > cpu.svg

# Per-process
perf record -F 99 -p <pid> -g -- sleep 30
```
`-F 99` samples at 99 Hz (avoids lock-step with 100 Hz kernel tick).
`-g` captures call graphs. `-a` profiles all CPUs.

**perf_event_paranoid and permissions:**
```bash
cat /proc/sys/kernel/perf_event_paranoid
# 2 = no kernel profiling without root (RHEL default)
# 1 = allow kernel profiling for normal users (needed for -a)
# 0 = full access
# -1 = no restrictions

# Temporary unlock for a session:
sysctl kernel.perf_event_paranoid=1
```

**RHEL9 vs RHEL10 perf stat comparison pattern:**
```bash
# Run on both hosts at same load; compare IPC and %sys attribution
perf stat -a -e cycles,instructions,context-switches,page-faults,\
cache-misses,branch-misses -I 1000 sleep 30 > perf_stat_rhel9.txt
```
If IPC is the same but throughput differs, the bottleneck is not compute
efficiency — look at scheduling latency and network stack. If IPC drops, look
at cache miss rate and memory bandwidth.

**RHEL version note.** Event names differ slightly between kernel versions.
If a named event fails: `perf list | grep cache` to find the equivalent.
`perf stat --metric-group TopdownL1` requires kernel >=5.4 for the metric
group syntax.

## Pointers
- perf wiki tutorial: https://perf.wiki.kernel.org/index.php/Tutorial
- Related units: `tma-top-down-analysis`, `mpstat-sar-cpu-breakdown`, `flame-graph-interpretation`
- Annex raw: none
