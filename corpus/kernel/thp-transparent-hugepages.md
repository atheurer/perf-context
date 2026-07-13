---
id: thp-transparent-hugepages
title: "Transparent Huge Pages: defaults, overhead, and RHEL version changes"
type: concept
domain: kernel
tags: [memory-pressure, low-ipc, high-sys-cpu]
source_id: kernel-docs
source_url: https://www.kernel.org/doc/html/latest/admin-guide/mm/transhuge.html
source_license: GPL-2.0
license_verified: false
track: core
applicability:
  kernel: "any; THP default mode differs between distro releases — always verify"
  hardware: "x86_64 (2M pages); aarch64 (2M pages)"
  software: "workloads with large contiguous allocations benefit; GC-heavy runtimes may regress"
tokens:
  abstract: 45
  digest: 450
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# Transparent Huge Pages: defaults, overhead, and RHEL version changes

## Abstract
Transparent Huge Pages (THP) automatically promotes 4K page mappings to 2M
pages to reduce TLB pressure for large working sets. The default mode differs
between RHEL versions and can be a hidden variable in OS comparisons. THP
helps bandwidth-bound workloads with large, contiguous allocations; it hurts
allocator-heavy workloads via khugepaged CPU overhead and memory fragmentation.

## Digest
**Checking current mode:**
```bash
cat /sys/kernel/mm/transparent_hugepage/enabled
# [always] madvise never   ← always is default on older RHEL
# always [madvise] never   ← madvise is default on newer RHEL/upstream
```

**Three modes:**
- `always` — kernel promotes any eligible anonymous mapping to 2M pages via
  khugepaged. Maximizes TLB coverage; khugepaged CPU overhead is real.
- `madvise` — only promotes regions explicitly tagged with `madvise(MADV_HUGEPAGE)`.
  Lets applications opt in; JVM, databases, and Redis typically do this.
- `never` — THP disabled. Maximum determinism; useful for latency-sensitive
  workloads where khugepaged stalls are unacceptable.

**RHEL defaults** [distiller-added, verify on actual hosts]:
- RHEL9: `always` has been the traditional default; some RHEL9.x versions
  changed to `madvise`. Verify with the above command.
- RHEL10: moving toward `madvise` as default. Verify on actual host.

**khugepaged overhead.** The kernel daemon `khugepaged` periodically scans
process address spaces looking for 4K page clusters to collapse into 2M pages.
This causes brief (<1ms) stalls in the process being scanned and uses CPU time
proportional to allocation rate. Workloads with rapid allocation/deallocation
(JVM GC, Go GC, Redis RESP parsing) see the most overhead.

**Detecting THP activity:**
```bash
# THP allocation and collapse counters
grep -E '^thp_' /proc/vmstat

# khugepaged stats
cat /sys/kernel/mm/transparent_hugepage/khugepaged/pages_collapsed

# Is khugepaged burning CPU?
top -p $(pgrep khugepaged)
```

**For RHEL9 vs RHEL10 comparisons.** If THP mode differs between the two hosts,
it is a confound. Standardize by setting the same mode on both:
```bash
echo madvise > /sys/kernel/mm/transparent_hugepage/enabled
```
For uperf network throughput tests, THP impact is usually minimal because the
working set is small (message buffers, socket buffers). If %sys or memory metrics
differ between RHEL9 and RHEL10, check THP mode, but treat it as a secondary
candidate after scheduler and mitigation differences.

**THP and TLB pressure.** When THP collapses pages, TLB coverage improves: the
same 48-entry L1 DTLB covers 48 × 2MB = 96MB with huge pages vs 48 × 4KB = 192KB
with base pages. For workloads with >200MB working sets and random access patterns,
THP is often net positive. See `tlb-pressure-hugepages` for measurement.

## Pointers
- Kernel doc: `Documentation/admin-guide/mm/transhuge.rst`
- Related units: `mglru-page-reclaim`, `tlb-pressure-hugepages`, `rhel9-rhel10-kernel-delta`
- Annex raw: none
