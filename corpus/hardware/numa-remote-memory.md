---
id: numa-remote-memory
title: "NUMA topology: remote memory latency, bandwidth, and placement"
type: concept
domain: hardware
tags: [numa-remote, p99-tail, low-ipc, memory-pressure]
source_id: drepper-memory
source_url: https://people.freedesktop.org/~drepper/cpumemory.pdf
source_license: all-rights-reserved
license_verified: false
track: digest
applicability:
  kernel: any
  hardware: multi-socket x86_64 (2+ NUMA nodes); AMD EPYC with CCD sub-NUMA clustering
  software: any
tokens:
  abstract: 48
  digest: 480
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# NUMA topology: remote memory latency, bandwidth, and placement

## Abstract
On multi-socket servers, memory attached to a different CPU socket (remote NUMA
node) has 1.5–2× higher latency and lower bandwidth than local memory. A
process whose threads run on socket 0 but whose memory was allocated on socket 1
pays this penalty on every cache miss. NUMA misplacement silently degrades
throughput and raises p99 latency without any obvious CPU saturation signal.

## Digest
**Topology discovery:**
```bash
numactl --hardware        # node distances, memory per node
lscpu | grep -i numa      # NUMA node count and CPU-to-node mapping
numactl --show            # current process's memory policy
```
The `numactl --hardware` distance matrix shows relative latency between nodes.
Distance 10 = local; distance 20–30 = remote (two-hop on typical dual-socket).
AMD EPYC with sub-NUMA clustering (SNC) may show 4+ nodes per socket.

**Detecting NUMA misplacement:**
```bash
# Per-process NUMA miss rate
numastat -p <pid>

# System-wide NUMA misses (NUMA_MISS / NUMA_HIT ratio)
numastat

# Kernel automatic migration activity
grep numa /proc/vmstat | grep -E 'numa_miss|numa_hit|numa_pages_migrated'

# sar -B shows pgmigrate (automatic NUMA migration events)
sar -B 1 30 | grep -E 'pgmigrate|numafault'
```
`NUMA_MISS` / (`NUMA_HIT` + `NUMA_MISS`) > 5% indicates significant remote
access and is worth investigating.

**Placement tools:**
```bash
# Pin a process to socket 0 CPUs and socket 0 memory
numactl --cpunodebind=0 --membind=0 -- <command>

# Pin memory to preferred node but allow remote on overflow
numactl --preferred=0 -- <command>

# Interleave memory across nodes (useful for bandwidth-bound, uniform-access workloads)
numactl --interleave=all -- <command>
```

**When interleave helps vs hurts.** Interleave (`--interleave=all`) distributes
allocations round-robin across nodes — good for bandwidth-bound workloads that
access data uniformly (matrix multiply, streaming) because it aggregates DRAM
bandwidth across sockets. Bad for latency-sensitive workloads with hot working
sets (interleaving means 50% of accesses are remote).

**Kernel automatic NUMA balancing.** The kernel's `numa_balancing` scans
process memory periodically and migrates pages toward the CPU accessing them.
This helps for long-running steady-state workloads. It adds overhead (scan
cost, page fault on first access after migration) and can hurt latency-sensitive
workloads. Check: `cat /proc/sys/kernel/numa_balancing`. Disable for latency-
sensitive benchmarks: `sysctl kernel.numa_balancing=0`.

**AWS note.** c5n.18xlarge instances have two NUMA nodes. Confirm:
`numactl --hardware` inside the instance. uperf client/server processes may
span both nodes depending on scheduler placement. If `numastat -p <uperf_pid>`
shows high `NUMA_MISS`, pin with `numactl --cpunodebind=0 --membind=0`.

**Latency numbers** [distiller-added, platform-dependent]:
- Local DDR4: ~80–90 ns
- Remote DDR4 (2-socket): ~130–160 ns
- DDR5 generation is faster but remote penalty ratio similar

## Pointers
- Ulrich Drepper, "What Every Programmer Should Know About Memory": https://people.freedesktop.org/~drepper/cpumemory.pdf
- Related units: `numa-balancing-kernel`, `memory-bandwidth-llc`, `rhel9-rhel10-kernel-delta`
- Annex raw: none
