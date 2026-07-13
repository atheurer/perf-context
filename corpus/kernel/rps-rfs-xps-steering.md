---
id: rps-rfs-xps-steering
title: "Network IRQ steering: RPS, RFS, and XPS configuration"
type: tool
domain: kernel
tags: [irq-storm, softirq-saturation, packet-drops, high-sys-cpu]
source_id: kernel-docs
source_url: https://www.kernel.org/doc/html/latest/networking/scaling.html
source_license: GPL-2.0
license_verified: false
track: core
applicability:
  kernel: "RPS/RFS: >=2.6.35; XPS: >=3.3"
  hardware: "all NICs benefit from RPS; multi-queue NICs should use HW RSS instead"
  software: any
tokens:
  abstract: 46
  digest: 500
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# Network IRQ steering: RPS, RFS, and XPS configuration

## Abstract
When a single-queue NIC or an imbalanced multi-queue NIC pins all packet
processing to one CPU, RPS (Receive Packet Steering) redistributes softirq
work across CPUs in software. RFS additionally routes packets to the CPU that
owns the receiving socket, improving cache locality. XPS does the same for
transmit. These are the primary tools for fixing the "one core pegged in
softirq" pattern on servers with insufficient or misconfigured hardware queues.

## Digest
**Diagnosis first.** Before configuring steering, confirm the problem:
```bash
# Is hardware already distributing across queues?
ethtool -l eth0      # "Combined: N" — if N > 1, HW RSS may be sufficient
grep eth0 /proc/interrupts   # one line per queue; check per-CPU distribution
mpstat -P ALL 1 5    # look for %soft concentration on one CPU
```
If the NIC has multiple combined queues and interrupts are balanced, RPS adds
overhead for no gain. Use RPS only when HW RSS is unavailable or insufficient.

**RPS — software receive-side scaling.** Hashes each packet's flow ID to a CPU
bitmask, distributing softirq processing without requiring multiple NIC queues.
```bash
# Enable RPS on all receive queues for eth0 — bitmask f = CPUs 0-3
for f in /sys/class/net/eth0/queues/rx-*/rps_cpus; do echo f > $f; done

# For more CPUs — e.g. ff = CPUs 0-7
for f in /sys/class/net/eth0/queues/rx-*/rps_cpus; do echo ff > $f; done
```
The bitmask is hex; `ff` enables CPUs 0–7. Match the mask to your socket's
CPU range to avoid cross-NUMA traffic.

**RFS — receive flow steering.** Routes packets to the CPU currently running
the socket's application thread, improving LLC hit rate for the payload.
```bash
# Global flow table size (power of 2, ≥ max concurrent connections)
sysctl -w net.core.rps_sock_flow_entries=32768

# Per-queue flow count (global / number of rx queues)
for f in /sys/class/net/eth0/queues/rx-*/rps_flow_cnt; do echo 4096 > $f; done
```
RFS requires RPS to be enabled first. The combination (RPS+RFS) is typically
what Red Hat recommends in `network-throughput` tuned profiles.

**XPS — transmit packet steering.** Maps transmit queues to CPU sets, keeping
a CPU's transmit traffic on its local queue. Usually configured automatically
by the driver on multi-queue NICs. Manual config:
```bash
# Map tx queue 0 to CPU 0 only
echo 1 > /sys/class/net/eth0/queues/tx-0/xps_cpus
```

**Verification after configuration:**
```bash
# softirq distribution should now spread across CPUs
watch -n 1 'cat /proc/softirqs | grep NET_RX'
mpstat -P ALL 1 5    # %soft should distribute, not pile on one CPU
```

**RHEL defaults.** The `network-throughput` tuned profile enables RPS/RFS with
a broad CPU mask. Verify with `tuned-adm profile_info network-throughput | grep
rps`. If uperf shows one-core softirq saturation despite the profile being
active, check that the profile was applied after the NIC came up (tuned applies
on device creation).

**When steering doesn't help.** If `%soft` is evenly distributed but still
high system-wide, the bottleneck is aggregate packet-processing capacity, not
distribution. Options: fewer, larger messages (reduce packet rate); NIC offloads
(GRO/GSO, check with `ethtool -k eth0`); or DPDK/kernel bypass.

## Pointers
- Kernel doc: `Documentation/networking/scaling.rst`
- Related units: `irq-softirq-napi`, `mpstat-sar-cpu-breakdown`
- Annex raw: none
