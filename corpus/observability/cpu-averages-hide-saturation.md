---
id: cpu-averages-hide-saturation
title: "Host-wide CPU averages hide per-CPU saturation: the single-stream bottleneck trap"
type: concept
domain: observability
tags: [high-sys-cpu, softirq-saturation, irq-storm, low-cpu-low-throughput, throughput-collapse]
source_id: gregg-site
source_url: https://www.brendangregg.com/usemethod.html
source_license: all-rights-reserved
license_verified: false
track: digest
applicability:
  kernel: any
  hardware: any multi-core system
  software: any single-stream or few-stream network/IO workload
tokens:
  abstract: 55
  digest: 530
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# Host-wide CPU averages hide per-CPU saturation: the single-stream bottleneck trap

## Abstract
A host-wide CPU utilization of 20% does not mean the workload has 80% CPU
headroom. A single CPU pinned at 100% — handling all softirq processing for a
single-stream network flow, or serving as the sole IRQ target for a NIC queue —
is a hard throughput ceiling regardless of what the other 63 CPUs are doing.
When attributing performance differences between OS versions or configurations,
always compare the *hottest* per-CPU breakouts, not the host-wide means.

## Digest
**The structural problem.** `mpstat` aggregate (no `-P ALL`) and CDM
`busy-cpu` without per-CPU breakout both compute means across all CPUs.
For a 64-core host running a single uperf stream:
- All CPUs average: 3% busy (2 CPUs at ~100%, 62 CPUs nearly idle)
- Conclusion from average: "plenty of headroom"
- Actual situation: NIC softirq CPU saturated, throughput ceiling hit

The average is mathematically correct and operationally useless.

**When this matters most — single-stream network tests.** A single TCP stream
is processed by one NIC queue, whose interrupts are delivered to one CPU. That
CPU handles all softirq (NET_RX) processing for the stream. Its `%soft` column
hits 100%; no other CPU can help. Throughput is bounded by that one core's
packet-processing capacity — typically 10–15 Gbps for a modern kernel on a
single core without busy-poll. Adding threads or increasing message size
eventually saturates this CPU before the NIC link is saturated.

**Multi-stream tests distribute differently.** With multiple streams (threads),
RSS or RPS distributes packets across multiple NIC queues and CPUs. The
bottleneck is the aggregate across those CPUs, and host-wide means become more
meaningful. Always check the run configuration — thread count and stream count
determine which analysis is appropriate.

**Discriminating commands:**
```bash
# Per-CPU breakdown during benchmark — look for any CPU at or near 100%
mpstat -P ALL 1 30

# Which CPU is taking NIC interrupts?
watch -n 1 'grep -E "eth|ens|eno" /proc/interrupts'

# softirq counts per CPU — which CPU processes NET_RX?
watch -n 1 'cat /proc/softirqs | grep NET_RX'

# CDM query equivalent: use breakout=num to get per-CPU metrics
# instead of the default host-wide aggregate
```

**OS-version comparison trap.** When comparing RHEL9 to RHEL10 on a single-
stream uperf test:
- Host-wide `busy-cpu` delta: "RHEL10 uses 0.8 more CPUs host-wide" → noise
- Per-CPU view: "RHEL10's softirq CPU sits at 98% vs RHEL9's 89%" → bottleneck

The per-CPU view reveals whether the bottleneck CPU composition changed (more
`%soft` → IRQ/softirq path; more `%sys` → kernel overhead/mitigations).
A change in IRQ affinity between OS versions (e.g., irqbalance defaults,
NIC driver queue configuration) can move the bottleneck CPU and change its
composition — making it look like an efficiency difference when it is actually
a placement difference.

**The hottest-CPU rule.** When CPU is a candidate explanation:
1. Get per-CPU data for both systems during the benchmark
2. Find the hottest CPU in each system (highest `%usr + %sys + %soft + %irq`)
3. Compare the *composition* of that hottest CPU between systems
4. Note whether the hottest CPU is the same role (softirq, application thread,
   etc.) in both systems — if the role changed, IRQ placement changed

**Normalization complement.** Per-CPU saturation detection answers "is one CPU
the ceiling?" — combine it with efficiency normalization (sys-CPUs per Gbps)
to determine whether the saturated CPU is *doing the same work more expensively*
or just *handling more traffic* because of placement. See `mpstat-sar-cpu-breakdown`
for column semantics and `irq-softirq-napi` for the softirq saturation model.

## Pointers
- Related units: `mpstat-sar-cpu-breakdown`, `irq-softirq-napi`, `rps-rfs-xps-steering`, `use-method`
- Annex raw: none
