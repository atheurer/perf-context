---
id: mpstat-sar-cpu-breakdown
title: "mpstat/sar CPU breakdown: reading user/sys/softirq/irq/iowait correctly"
type: tool
domain: observability
tags: [high-sys-cpu, irq-storm, softirq-saturation, iowait-high, high-user-cpu]
source_id: sysstat
source_url: https://github.com/sysstat/sysstat
source_license: GPL-2.0
license_verified: false
track: core
applicability:
  kernel: any
  hardware: any
  software: any
tokens:
  abstract: 44
  digest: 510
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# mpstat/sar CPU breakdown: reading user/sys/softirq/irq/iowait correctly

## Abstract
`mpstat` and `sar -u` break CPU time into user, sys, softirq, irq, iowait,
steal, and idle. Each column answers a different diagnostic question. Misreading
iowait (not a disk-speed metric) or softirq (IRQ imbalance, not load) is a
common investigation error. When crucible collects sar/mpstat data, these are
the columns that explain *where* CPU time goes between two benchmark runs.

## Digest
**Column semantics** (`mpstat -P ALL 1` or `sar -P ALL 1`):

| Column | Meaning | High value suggests |
|---|---|---|
| `%usr` | User-mode time | CPU-bound application code |
| `%sys` | Kernel-mode time | Syscall overhead, scheduler, page faults, mitigations |
| `%iowait` | Idle while ≥1 runnable task waits on I/O | I/O-blocked workload (NOT disk speed) |
| `%irq` | Hardware interrupt service | High interrupt rate (NIC, storage) |
| `%soft` | Softirq service (NET_RX/TX, BLOCK, etc.) | Network RX/TX processing, NAPI |
| `%steal` | Time stolen by hypervisor | VM resource contention (AWS: rare on dedicated) |
| `%idle` | Truly idle | CPU headroom available |

**Metric units in crucible CDM output.** When the CDM query returns mpstat
`busy-cpu` values, the unit is *CPUs busy*, not percent:
- `1.0` = one CPU fully busy (whether that's one core at 100% or three cores at 33% each)
- With a `hostname` breakout, you get one value per host (still in CPUs)
- With a `num` breakout, you get per-CPU values with a max of `1.0` each

This differs from the raw `mpstat` `%` columns. To convert a CDM busy-cpu value
to "% of all CPUs": `value / cpu_count × 100`.

**Diagnostic patterns:**

*High `%sys` system-wide* → kernel is doing more work: increased syscall rate
(check `perf stat -e syscalls:sys_enter_*`), more page faults (`perf stat -e
page-faults`), or higher mitigation overhead (compare RHEL9 vs RHEL10 on the
same hardware — `eibrs` vs `retpoline` can differ). Also the signature of
scheduler overhead (many context switches inflating kernel time).

*High `%soft` on one CPU* → IRQ imbalance. One CPU is handling all network
softirq processing. Check `/proc/interrupts` per-CPU distribution and
`/proc/softirqs` NET_RX column. Fix with RPS/RFS or NIC multi-queue.

*High `%iowait`* — **common misread**: iowait measures time a CPU spends idle
while *some runnable task* on that CPU is blocked in I/O. It does NOT measure
disk latency or throughput. A CPU can show 0% iowait while disk is maxed out
(if the waiting task is on a different CPU), or show 80% iowait on fast NVMe
(if one synchronous task is blocking). To measure disk speed, use `iostat -x`
or `biolatency`.

*`%usr` + `%sys` + `%soft` + `%irq` < 30%, `%idle` > 70%* with poor throughput
→ not CPU-bound; look for lock contention, I/O blocking, or coordinated omission
in the load generator.

**Commands for RHEL9 vs RHEL10 comparison:**
```bash
# Per-CPU breakdown every second for 30s
mpstat -P ALL 1 30

# System-wide aggregate
sar -u 1 30

# All metrics (CPU + memory + network)
sar -A 1 30 > sar-output.txt

# Softirq delta (useful for network tuning)
watch -n 1 'cat /proc/softirqs | grep -E "NET_RX|NET_TX|BLOCK"'
```

**RHEL9 vs RHEL10 delta to watch.** On the same hardware and workload, if RHEL10
shows higher `%sys` than RHEL9, the candidate causes in order are: (1) EEVDF
scheduler overhead differences, (2) Spectre mitigation generation change (check
`/sys/devices/system/cpu/vulnerabilities/*`), (3) new kernel subsystems active
by default. Do not attribute to "RHEL10 is slower" without checking each cause.

## Pointers
- sysstat man pages: `man mpstat`, `man sar`
- Related units: `eevdf-vs-cfs`, `irq-softirq-napi`, `rps-rfs-xps-steering`, `pidstat-context-switches`
- Annex raw: none
