---
id: false-sharing-coherence
title: "Cache false sharing: detection with perf c2c, patterns, and fixes"
type: concept
domain: hardware
tags: [false-sharing, low-ipc, high-sys-cpu]
source_id: drepper-memory
source_url: https://people.freedesktop.org/~drepper/cpumemory.pdf
source_license: all-rights-reserved
license_verified: false
track: digest
applicability:
  kernel: any
  hardware: multi-core x86_64 (any cache-coherent multi-processor)
  software: multi-threaded C/C++, Go, Java applications
tokens:
  abstract: 45
  digest: 450
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# Cache false sharing: detection with perf c2c, patterns, and fixes

## Abstract
False sharing occurs when two threads on different CPUs write to different
variables that happen to occupy the same 64-byte cache line. Each write
invalidates the line on the other CPU, causing MESI protocol traffic and
serializing what would otherwise be independent operations. The symptom is
unexpectedly poor multi-threaded scaling with low IPC on the contending cores.

## Digest
**Mechanism.** Cache coherence operates at cache line granularity (64 bytes on
x86). If thread A on CPU0 writes field `x` at offset 0 of a struct and thread B
on CPU1 writes field `y` at offset 4, they share a cache line. Every write by A
invalidates the line in CPU1's cache, forcing B to re-fetch it — and vice versa.
The workload sees this as a series of LLC misses with the HITM (hit in modified)
state, which is significantly more expensive than a normal LLC miss.

**Detection with perf c2c:**
```bash
# Record with PEBS (requires root; Intel Xeon or AMD Zen2+)
perf c2c record -a --all-user -- sleep 10

# Report: shows cache lines with high HITM rates
perf c2c report --stdio --sort=hitm | head -60
```
Key columns in the report:
- `HITM%` — percentage of loads that hit a modified line from another core
- `CL addr` — cache line physical address
- `Load/Store` — instructions accessing the hot line

Any line with HITM% > 10% and high access count is a false sharing candidate.

**Common patterns:**
1. *Counter arrays*: `int counters[N_THREADS]` — each element is 4 bytes;
   threads 0 and 1 share a line if N_THREADS is dense.
   Fix: pad to cache line: `struct { int val; char pad[60]; } counters[N_THREADS]`.
2. *Struct with mixed access patterns*: a struct has a read-mostly field and a
   write-frequently field on the same line. Fix: split into two structs or
   reorder fields.
3. *Lock + data*: a mutex and the data it protects on the same line. Lock
   acquisition by one thread invalidates data cached by another.

**Fix patterns:**
```c
// Padding to force cache line alignment (C11)
struct per_cpu_counter {
    long value;
    char _pad[64 - sizeof(long)];  // explicit padding
} __attribute__((aligned(64)));

// Or use alignas (C++11/C11)
alignas(64) struct per_cpu_counter counters[N_THREADS];
```
In Go: `//go:noescape` and manual struct padding. In Java: use `@Contended`
annotation (JDK8+) which pads fields automatically.

**True sharing vs false sharing.** True sharing: two threads genuinely share
data (producer writes, consumer reads the same field). False sharing: two
threads write *different* fields that collide in the cache line. `perf c2c`
distinguishes them: true sharing shows high load hits on modified lines from
the *same* cache line field; false sharing shows hits from *different offsets*.

**Performance impact.** On a 2-socket server with NUMA, remote HITM (the
modified line is on a different socket) costs ~300–500 cycles. Local HITM (same
socket, different core) costs ~40–60 cycles. Either is much more expensive than
an L3 hit (~30 cycles) or local DRAM (~80 cycles).

## Pointers
- perf c2c documentation: `man perf-c2c`
- Related units: `numa-remote-memory`, `perf-stat-record`, `memory-bandwidth-llc`
- Annex raw: none
