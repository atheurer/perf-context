---
id: biolatency-iostat
title: "Block I/O latency: biolatency (BCC), iostat -x, and disk diagnosis"
type: tool
domain: observability
tags: [iowait-high]
source_id: bcc
source_url: https://github.com/iovisor/bcc/blob/master/tools/biolatency_example.txt
source_license: Apache-2.0
license_verified: false
track: core
applicability:
  kernel: ">=4.9 (BPF for biolatency); iostat: any"
  hardware: any block device (NVMe, SSD, HDD, virtual disk)
  software: I/O-bound workloads
tokens:
  abstract: 44
  digest: 440
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# Block I/O latency: biolatency (BCC), iostat -x, and disk diagnosis

## Abstract
`iostat -x` and `biolatency` provide complementary views of block I/O
performance: iostat gives aggregate rates and queue depth; biolatency gives the
full latency distribution. The critical interpretation rule for iostat is that
`aqu-sz` (average queue size) > 1 means the device is saturated, and `%util`
at 100% on SSDs does not mean the device is slow — it measures time, not
throughput. When iowait is high, start with iostat to determine whether I/O is
actually occurring, then use biolatency to profile the latency distribution.

## Digest
**iostat -x interpretation:**
```bash
iostat -x 1 30
```
Key columns and what they mean:

| Column | Meaning | Alarm threshold |
|---|---|---|
| `aqu-sz` | Average request queue size at device | > 1 sustained = saturated |
| `r_await` / `w_await` | Average read/write latency (ms) incl. queue | > 1ms NVMe, > 10ms SSD is high |
| `%util` | % of time the device was busy | 100% does NOT mean saturated (see below) |
| `rkB/s` / `wkB/s` | Read/write throughput in KB/s | Compare to device spec |
| `r/s` / `w/s` | IOPS | Compare to device IOPS spec |

**The `%util` trap.** `%util` measures the fraction of time at least one I/O
request was in flight. For a fast NVMe with queue depth 32, `%util` hits 100%
at low IOPS because each request completes in microseconds. The device is not
saturated. Use `aqu-sz > 1` as the saturation signal, not `%util`.

**biolatency — full latency distribution:**
```bash
# System-wide block I/O latency histogram, 30 seconds
biolatency 30

# Per-disk breakdown
biolatency -D 30

# Filter to reads only
biolatency -r 30
```
Output is a log-scale histogram: `usecs` buckets with counts and a visual bar.
NVMe expected p99: <1ms. SATA SSD: <5ms. HDD: <20ms. If p99 >> these values,
investigate queue depth and I/O scheduler.

**High iowait checklist:**
1. Is any I/O actually happening? `iostat -x 1` — if rkB/s + wkB/s near zero
   with high iowait, the waiting task may be in a sync operation with no real
   I/O (lock, pipe, etc.).
2. Is the device saturated? `aqu-sz > 1` sustained.
3. What is the latency distribution? `biolatency -D 30` — is p99 > 10ms?
4. Is the I/O scheduler appropriate? `cat /sys/block/nvme0n1/queue/scheduler`
   — NVMe should use `none` or `mq-deadline`, not `bfq`.
5. Is queue depth sufficient? `cat /sys/block/nvme0n1/queue/nr_requests` —
   for NVMe, 1024+ is typical.

**fio baseline.** If iostat shows low throughput on an NVMe, verify with a
direct fio test to separate device speed from filesystem overhead:
```bash
fio --name=baseline --rw=randread --bs=4k --numjobs=4 --iodepth=32 \
    --runtime=30 --filename=/dev/nvme0n1 --direct=1 --ioengine=libaio
```

## Pointers
- BCC biolatency: https://github.com/iovisor/bcc/blob/master/tools/biolatency_example.txt
- `man iostat`
- Related units: `io-scheduler-block-layer`, `use-method`, `psi-pressure-stall`
- Annex raw: none
