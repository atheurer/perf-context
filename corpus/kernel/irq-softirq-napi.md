---
id: irq-softirq-napi
title: "IRQ and softirq processing: per-CPU budgets, NAPI, and saturation"
type: concept
domain: kernel
tags: [irq-storm, softirq-saturation, high-sys-cpu, packet-drops]
source_id: kernel-docs
source_url: https://www.kernel.org/doc/html/latest/networking/napi.html
source_license: GPL-2.0
license_verified: false
track: core
applicability:
  kernel: any
  hardware: any NIC
  software: any network-intensive workload
tokens:
  abstract: 50
  digest: 540
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# IRQ and softirq processing: per-CPU budgets, NAPI, and saturation

## Abstract
Network packet processing flows from NIC interrupt → hardirq → softirq → NAPI
poll loop. When one CPU handles all softirq work for a NIC, `%soft` pegs at
100% on that core while others stay idle. This is the primary cause of single-
core saturation at high network throughput even when overall CPU utilization
looks low. The fix is IRQ steering (see `rps-rfs-xps-steering`); the diagnosis
is `/proc/softirqs` and `mpstat -P ALL`.

## Digest
**Execution model.** A NIC raises a hardware interrupt; the kernel's hardirq
handler runs on the interrupted CPU (minimal work: acknowledge, schedule
softirq). The softirq (NET_RX, NET_TX) runs on the same CPU, either in the
interrupt return path or — if budget exhausted — in `ksoftirqd`. NAPI poll
is called from within NET_RX softirq: it processes up to `netdev_budget`
packets (default 300) per poll cycle before yielding. If the ring still has
packets, another softirq fires on the *same CPU*. The result: all NIC packet
processing is pinned to whichever CPU received the first interrupt.

**Saturation signature.** `mpstat -P ALL 1`:
```
CPU  %usr  %sys  %iowait  %irq  %soft  %idle
  0  25.0  10.0      0.0   1.0   63.0    1.0   ← all softirq here
  1   5.0   2.0      0.0   0.0    0.0   93.0
  2   5.0   2.0      0.0   0.0    0.0   93.0
```
One CPU at 100% with remaining CPUs idle means IRQ steering, not more CPUs, is
the fix. Throughput is bounded by one core's packet-processing capacity.

**Confirming the diagnosis:**
```bash
# Which CPU is taking NIC interrupts?
watch -n 1 'grep eth0 /proc/interrupts'

# softirq counts per CPU (watch NET_RX column)
watch -n 1 'cat /proc/softirqs'

# Rate of softirq events per CPU
sar -I ALL 1 5
```

**ksoftirqd.** When NAPI budget is exhausted within a single softirq, the
kernel defers to the `ksoftirqd/<cpu>` kernel thread. High `ksoftirqd` CPU
time (visible in `top` or `ps`) means the NIC is consistently saturating the
softirq budget — a sign of sustained overload on that CPU.

**Budget tuning.** `net.core.netdev_budget` (default 300) controls packets
processed per NAPI poll. Increasing it (e.g. 600–1200) can help throughput on
a single-queue setup at the cost of higher latency on the processing CPU. This
is a second-order fix; IRQ distribution is first.

**NAPI busy-poll.** For latency-sensitive sockets: `net.core.busy_read` /
`net.core.busy_poll` enable spinning on the NIC ring for a microsecond budget
instead of sleeping. Reduces wakeup latency at the cost of burning idle CPU.
Relevant for uperf/netperf stream tests where the receiving thread idles
between bursts.

**RHEL9 vs RHEL10.** The interrupt-to-softirq model is unchanged between the
two releases. If one release shows higher `%soft` on a single CPU it is
because IRQ affinity differs (check `/proc/irq/<N>/smp_affinity_list`) or
because the NIC driver queue configuration changed. Verify with
`ethtool -l <dev>` (combined queue count) on both hosts.

## Pointers
- Kernel doc: `Documentation/networking/napi.rst`
- Related units: `rps-rfs-xps-steering`, `mpstat-sar-cpu-breakdown`, `qdisc-ring-drops`
- Annex raw: none
