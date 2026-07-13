---
id: qdisc-ring-drops
title: "Network drops: NIC ring buffer overflow, qdisc drops, and diagnosis"
type: tool
domain: distributed
tags: [packet-drops, retransmits, softirq-saturation]
source_id: kernel-docs
source_url: https://www.kernel.org/doc/html/latest/networking/
source_license: GPL-2.0
license_verified: false
track: core
applicability:
  kernel: any
  hardware: any NIC
  software: network-intensive workloads; UDP streaming; high-throughput TCP
tokens:
  abstract: 47
  digest: 510
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# Network drops: NIC ring buffer overflow, qdisc drops, and diagnosis

## Abstract
Network packet drops occur at several distinct points: the NIC ring buffer
(driver-level), the qdisc (kernel transmit queue), and the socket receive
buffer. Each has its own counter and its own fix. Identifying which layer is
dropping before tuning is essential — increasing rmem when the problem is the
ring buffer wastes time and misses the real fix.

## Digest
**Drop taxonomy and where to look:**

| Drop type | Counter | Fix |
|---|---|---|
| NIC ring overflow (rx) | `ethtool -S <dev> \| grep -i miss\|drop\|error` | `ethtool -G <dev> rx 4096` |
| NIC ring overflow (tx) | `ethtool -S <dev> \| grep tx_dropped` | `ethtool -G <dev> tx 4096` |
| qdisc drop | `tc -s qdisc show dev <dev>` — `dropped` counter | Increase qdisc limit or change scheduler |
| Socket recv buffer | `ss -s` (recv-Q overflow), `netstat -su` UDP errors | `sysctl net.core.rmem_max` |
| TCP retransmit | `ss -ti` retrans field, `nstat -az TcpRetransSegs` | Reduce loss source; tune rmem/wmem |

**Step 1: Check the NIC ring first.**
```bash
# Current ring sizes
ethtool -g eth0     # Pre-set max and current rx/tx ring entries

# Driver drop counters (names vary by driver)
ethtool -S eth0 | grep -iE 'miss|drop|error|discard|no_buff'

# Also check ip -s link
ip -s link show eth0   # RX errors, dropped
```
Ring overflow is the most common cause of drops at high packet rates. Increase
with `ethtool -G eth0 rx 4096` (persist via `/etc/NetworkManager/` or udev
rule). Maximum ring size is hardware-dependent; query with `ethtool -g`.

**Step 2: Check qdisc.**
```bash
tc -s qdisc show dev eth0
# Look for: dropped N — any non-zero drop count is significant at steady state
```
The default qdisc on most RHEL systems is `fq_codel` or `pfifo_fast`. For pure
throughput with no fairness requirements, `noqueue` or `fq` may reduce latency.
Increasing `txqueuelen` (`ip link set eth0 txqueuelen 10000`) raises the pfifo
limit before drops occur.

**Step 3: Check socket buffers (TCP retransmits).**
```bash
nstat -az | grep -E 'TcpRetrans|UdpInErrors'
ss -ti | grep retrans       # per-socket retransmit count
```
For uperf TCP stream tests, retransmits indicate loss upstream (NIC ring or
qdisc) rather than socket buffer insufficiency. Fix the ring/qdisc first;
tune rmem/wmem only if the ring is fine.

**Isolating the drop point during uperf.** Take a baseline of all counters
before the run, snapshot after, and diff:
```bash
# Before
ethtool -S eth0 > drops_before.txt
tc -s qdisc show dev eth0 >> drops_before.txt
nstat -az >> drops_before.txt

# After run
ethtool -S eth0 > drops_after.txt
# diff and look for increasing counters
```

**RHEL9 vs RHEL10 differences.** Default qdisc may differ (RHEL10 may default
`fq_codel` where RHEL9 used `pfifo_fast`). fq_codel's AQM can drop packets
under load to manage latency — this is intentional but shows as drops in the
counter. If drops appear only on RHEL10, check `tc qdisc show` for the active
qdisc type on each host.

## Pointers
- Kernel doc: `Documentation/networking/`
- Related units: `irq-softirq-napi`, `rps-rfs-xps-steering`, `tcp-incast`
- Annex raw: none
