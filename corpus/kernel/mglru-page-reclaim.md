---
id: mglru-page-reclaim
title: "MGLRU: multi-generational LRU page reclaim (RHEL10 default)"
type: concept
domain: kernel
tags: [memory-pressure, swap-thrash, throughput-collapse]
source_id: lwn
source_url: https://lwn.net/Articles/881876/
source_license: all-rights-reserved
license_verified: false
track: digest
applicability:
  kernel: "upstream >=6.1 (MGLRU merged); RHEL10 (kernel-6.12-based): yes, enabled by default; RHEL9: backported in RHEL9.3+ (kernel >=5.14.0-362), disabled by default — enable with `echo y > /sys/kernel/mm/lru_gen/enabled`; verify: `cat /sys/kernel/mm/lru_gen/enabled`"
  hardware: any
  software: any
tokens:
  abstract: 48
  digest: 490
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# MGLRU: multi-generational LRU page reclaim (RHEL10 default)

## Abstract
MGLRU (Multi-Generational LRU) replaces the kernel's traditional two-list
active/inactive page reclaim in Linux 6.1+. RHEL10 enables it by default;
RHEL9 backported it in 9.3 but leaves it disabled. On memory-pressured
workloads, MGLRU changes which pages are evicted, reducing refault rates.
Its presence or absence is a variable to control when comparing RHEL9 and RHEL10.

## Digest
**Why the old LRU was insufficient.** The classic active/inactive two-list LRU
struggles when the working set is larger than RAM and access patterns are mixed:
a large sequential scan promoting many pages to the active list evicts pages
from actually-hot anonymous memory. The result is elevated `workingset_refault`
(pages evicted then faulted back in shortly after), which shows as iowait and
cache-miss pressure even when total memory usage looks reasonable.

**How MGLRU works.** MGLRU maintains multiple generations of pages (typically
4), aging them based on recency of access via a combination of hardware access
bits and software heuristics. Pages are promoted to younger generations on
access; pages in the oldest generation are eviction candidates. This reduces
false evictions of hot pages and allows better handling of mixed hot/cold
workloads. [distiller-added: the implementation tracks generations per
`lru_gen_page` structures; the kernel doc is `Documentation/mm/multigen_lru.rst`.]

**RHEL version status:**
- RHEL10 (kernel-6.12): MGLRU enabled by default. `cat /sys/kernel/mm/lru_gen/enabled` → `0x0007` or non-zero.
- RHEL9.3+ (kernel >=5.14.0-362): backported but `disabled` by default → `0x0000`. Enable with `echo y > /sys/kernel/mm/lru_gen/enabled`.
- RHEL9 < 9.3: MGLRU not present.

**Detection and measurement.** Key `/proc/vmstat` counters that change with MGLRU active vs inactive:
```
grep -E 'workingset_refault|workingset_activate|pgpgin|pgpgout' /proc/vmstat
# workingset_refault_anon/file: pages evicted then re-faulted — lower is better
# workingset_activate: hot pages rescued from eviction

# sar -B 1 30 — watch pgscank (scanned) and pgsteal (evicted) rate
sar -B 1 30
```

**Workloads affected.** MGLRU helps most when:
- Working set exceeds available RAM (the common case in container-dense hosts)
- Mixed hot/cold access: a background bulk scan coexists with latency-sensitive foreground access
- File-backed workloads with irregular access patterns

MGLRU is largely neutral for workloads that fit comfortably in RAM or that are purely sequential. It can occasionally regress workloads where the heuristics misclassify pages — if RHEL10 shows higher refault counts than RHEL9, MGLRU tuning or disabling it (`echo n > /sys/kernel/mm/lru_gen/enabled`) can isolate the effect.

**When comparing RHEL9 vs RHEL10.** If memory pressure metrics differ between
the two runs (higher pgsteal, higher iowait), MGLRU state is a confound to
eliminate. Verify `lru_gen/enabled` on both hosts and standardize before
attributing differences to other causes.

## Pointers
- LWN "MGLRU merged into mainline": https://lwn.net/Articles/881876/
- LWN "Multigenerational LRU: the next steps": https://lwn.net/Articles/851817/
- Kernel doc: `Documentation/mm/multigen_lru.rst`
- Related units: `rhel9-rhel10-kernel-delta`, `thp-transparent-hugepages`
- Annex raw: none
