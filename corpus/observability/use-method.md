---
id: use-method
title: "USE Method: Utilization, Saturation, Errors for systematic resource investigation"
type: concept
domain: observability
tags: [high-sys-cpu, iowait-high, memory-pressure, throughput-collapse]
source_id: gregg-site
source_url: https://www.brendangregg.com/usemethod.html
source_license: all-rights-reserved
license_verified: false
track: digest
applicability:
  kernel: any
  hardware: any
  software: any
tokens:
  abstract: 46
  digest: 470
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# USE Method: Utilization, Saturation, Errors for systematic resource investigation

## Abstract
The USE Method structures performance investigation as a checklist: for every
system resource, measure Utilization (% busy), Saturation (queue depth or wait),
and Errors. It prevents the common failure mode of fixating on one metric while
missing the actual bottleneck resource. Apply it at the start of any
investigation before forming hypotheses.

## Digest
**The three metrics per resource:**
- **Utilization**: fraction of time the resource is busy (0–100%). At high
  utilization, queuing theory predicts nonlinear latency growth.
- **Saturation**: degree to which the resource has more work than it can
  handle right now — measured as queue length, wait time, or a boolean
  (backpressure). A resource can be 50% utilized but saturated if work arrives
  in bursts.
- **Errors**: error events (hardware errors, packet drops, I/O errors). Often
  zero in healthy systems; non-zero immediately narrows scope.

**Resources to check and their metrics:**

| Resource | Utilization | Saturation | Errors |
|---|---|---|---|
| CPU | `mpstat %usr+%sys` | `sar -q` runq-sz, load > CPU count | `perf stat` hw errors |
| Memory | `free -h` used/total | `sar -B` pgscan/pgsteal, swap used | ECC errors (`edac-util`) |
| Network | `sar -n DEV` rxkB/txkB vs NIC capacity | `tc -s qdisc` drops, retransmits | `ethtool -S` errors |
| Disk | `iostat -x` `%util` | `iostat -x` aqu-sz > 1 | `dmesg | grep error` |
| CPU scheduler | (no utilization metric) | `sar -q` runq-sz, `pidstat -w` involuntary cswch | — |

**Order of checking.** Check in this order, stop when you find saturation or
errors:
1. CPU — is any CPU saturated (util near 100% or load/core > 1)?
2. Memory — is the system paging out or reclaiming heavily?
3. Network — is the NIC at capacity, or dropping packets?
4. Disk — are I/O operations queuing (aqu-sz > 1 sustained)?

If all four are fine, the bottleneck is likely inside the application: lock
contention, GC pauses, or load-generator coordinated omission.

**USE limitations.** USE finds resource-level bottlenecks efficiently. It does
*not* directly find:
- Userspace lock contention (the CPU is "utilized" doing nothing useful while
  spinning)
- Algorithmic inefficiency (CPU is utilized doing real work, just wrong work)
- Coordinated omission hiding low load from the generator

For lock contention: off-CPU flame graphs (see `off-cpu-analysis`). For
coordinated omission: check the load generator methodology (see
`coordinated-omission`).

**Applying USE to a two-run comparison.** Run the USE checklist on both the
RHEL9 and RHEL10 results. If utilization differs at the same load, that is the
delta to explain — not a conclusion. The explanation requires identifying which
resource's utilization changed and why (scheduler overhead, mitigation cost,
page reclaim rate, etc.).

## Pointers
- Brendan Gregg, USE Method: https://www.brendangregg.com/usemethod.html
- Related units: `mpstat-sar-cpu-breakdown`, `hypothesis-driven-investigation`, `off-cpu-analysis`
- Annex raw: none
