---
id: flame-graph-interpretation
title: "CPU and off-CPU flame graph reading: interpretation and differential graphs"
type: tool
domain: observability
tags: [high-sys-cpu, high-user-cpu, lock-contention, throughput-collapse]
source_id: flamegraph
source_url: https://github.com/brendangregg/FlameGraph
source_license: CDDL-1.0
license_verified: false
track: core
applicability:
  kernel: any
  hardware: any
  software: any
tokens:
  abstract: 42
  digest: 440
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# CPU and off-CPU flame graph reading: interpretation and differential graphs

## Abstract
Flame graphs visualize profiling data as stacked call frames where width
represents time. The x-axis is not time order — it is the sampled population,
sorted alphabetically. A wide frame at any level means that stack consumed a
significant fraction of total profiling time. Differential flame graphs compare
two profiles to highlight regressions (red) and improvements (blue).

## Digest
**Reading a CPU flame graph.** Collect with `perf record -F 99 -a -g -- sleep 30`
and render with `flamegraph.pl`. Key interpretation rules:

- **Width = time fraction**, not time elapsed. A function 10% wide consumed 10%
  of profiling time.
- **The top of each tower** is where CPU time is actually spent — the leaf
  frames. Frames below are callers (context, not cost).
- **Flat tops** indicate a hot function with little deeper callstack — common for
  tight loops and spinlocks.
- **Tall narrow towers** indicate deep call chains with one hot leaf.
- **Wide base, narrow top** indicates a caller dispatching to many different
  callees — an orchestrator function that is not itself hot.
- **Kernel frames** appear at the top of the stack when the profiled process is
  inside a syscall. Wide kernel frames mean syscall overhead (relevant for
  Spectre mitigation cost comparisons).

**Generating:**
```bash
perf record -F 99 -a -g -- sleep 30
perf script | stackcollapse-perf.pl | flamegraph.pl --title "RHEL10 uperf" > cpu_rhel10.svg
```

**Off-CPU flame graph (width = blocked time):**
```bash
offcputime -K -U 30 | flamegraph.pl --color=io --title "Off-CPU RHEL10" > offcpu_rhel10.svg
```
Off-CPU graphs show where time is spent *not* running. The top frame is the
reason for blocking. Wide `futex_wait` = lock contention; wide `tcp_recvmsg` =
waiting for network data (expected for a stream test receiver).

**Differential flame graphs — comparing two runs:**
```bash
# Generate collapsed stacks for both runs
perf script --input=perf_rhel9.data | stackcollapse-perf.pl > stacks_rhel9.txt
perf script --input=perf_rhel10.data | stackcollapse-perf.pl > stacks_rhel10.txt

# Diff: red = more in RHEL10, blue = less in RHEL10
difffolded.pl stacks_rhel9.txt stacks_rhel10.txt | flamegraph.pl --negate > diff.svg
```
Red frames in the diff that are kernel-side scheduler functions confirm EEVDF
overhead. Red frames in the network stack confirm NIC processing cost change.

**Common misinterpretations:**
- *Narrow = infrequent*: wrong. Sampling rate matters. A function called 1000
  times per second at 1µs each appears narrow at 99 Hz sampling. Use `perf stat`
  for counting, flame graphs for where.
- *Alphabetical sort looks like time order*: it is not. Adjacent towers with
  similar names are sorted together, not consecutive in time.
- *Missing frames (broken stacks)*: frame pointer omission (`-O2` optimization
  drops frame pointers). Fix: compile with `-fno-omit-frame-pointer` or use
  DWARF unwinding (`perf record --call-graph dwarf`).

## Pointers
- FlameGraph repo: https://github.com/brendangregg/FlameGraph
- Brendan Gregg's flame graph introduction: https://www.brendangregg.com/flamegraphs.html
- Related units: `off-cpu-analysis`, `perf-stat-record`, `irq-softirq-napi`
- Annex raw: none
