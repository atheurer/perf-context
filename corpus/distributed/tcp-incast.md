---
id: tcp-incast
title: "TCP incast: many-to-one collapse, rmem/wmem tuning"
type: concept
domain: distributed
tags: [packet-drops, retransmits, p99-tail, throughput-collapse]
source_id: gregg-sysperf-book
source_url: https://www.brendangregg.com/systems-performance-2nd-edition-book.html
source_license: proprietary
license_verified: false
track: digest
applicability:
  kernel: any
  hardware: any data center NIC; more pronounced on shallow-buffer switches
  software: distributed systems with fan-in patterns (MapReduce, Ceph, clustered storage, k8s ingress)
tokens:
  abstract: 46
  digest: 450
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# TCP incast: many-to-one collapse, many-to-one collapse, rmem/wmem tuning

## Abstract
TCP incast occurs when many servers respond simultaneously to one receiver,
causing switch buffer overflow, packet drops, and TCP retransmit timeout (RTO)
delays of 200ms or more. Throughput collapses even though the network appears
otherwise healthy. Incast is a fan-in problem — not relevant to uperf client-
server pairs but critical in distributed storage, MapReduce, and Ceph patterns.

## Digest
**Mechanism.** A single client sends requests to N servers; all N respond
simultaneously. Their combined traffic exceeds the switch port's buffer,
causing drops. A dropped TCP segment triggers a retransmit timeout (RTO ≈ 200ms
with the minimum RTO floor) rather than fast retransmit, because many segments
are lost simultaneously and the TCP receiver cannot generate enough duplicate
ACKs to trigger fast retransmit. This serializes recovery and collapses goodput
even though individual links are underutilized.

**Detection:**
```bash
# Retransmit counters (check on receiving end)
nstat -az | grep TcpRetransSegs
ss -ti | grep retrans       # per-socket retransmit count

# Watch for RTO events (coarse but revealing)
ss -ti | grep rto

# Drop counters at the NIC (packets arriving but ring full)
ethtool -S eth0 | grep -iE 'miss|drop|no_buff'
```
The signature is: retransmits clustered in time, RTO near 200ms (the min_rto
floor), throughput that collapses from N Gbps to << 1 Gbps briefly then
recovers, repeating.

**Socket buffer tuning (first-order fix):**
```bash
# Increase receive buffer limits
sysctl -w net.core.rmem_max=134217728
sysctl -w net.ipv4.tcp_rmem='4096 87380 134217728'

# Increase transmit buffer
sysctl -w net.core.wmem_max=134217728
sysctl -w net.ipv4.tcp_wmem='4096 87380 134217728'

# Current tcp socket buffer sizes
ss -ti | grep rcv_space
```
Larger buffers absorb bursts at the receiver, reducing drops. This does not fix
the switch-buffer problem but reduces its impact by keeping the connection alive
longer.

**DCTCP (Datacenter TCP).** For datacenter networks with ECN-capable switches:
```bash
sysctl -w net.ipv4.tcp_congestion_control=dctcp
sysctl -w net.ipv4.tcp_ecn=1
```
DCTCP reacts to ECN marks before drops occur, reducing queue buildup. Requires
both endpoints and switch support.

**NIC ring buffer.** A large receive ring absorbs burst arrivals before the
kernel processes them:
```bash
ethtool -G eth0 rx 4096    # increase from default 512 or 1024
```

**Applicability to uperf tests.** A single-client, single-server uperf stream
test does not trigger incast. Incast becomes relevant when the benchmark uses
multiple servers sending to one client simultaneously, or in the CDM query path
where multiple data sources respond concurrently. If uperf tests show normal
retransmit counts, incast is not the cause.

## Pointers
- Related units: `qdisc-ring-drops`, `rps-rfs-xps-steering`
- DCTCP RFC: https://datatracker.ietf.org/doc/html/rfc8257
- Annex raw: none
