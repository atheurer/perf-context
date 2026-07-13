---
id: tuned-profiles-rhel
title: "tuned profiles in RHEL9 vs RHEL10: which sysctls change and why"
type: reference
domain: kernel
tags: [high-sys-cpu, low-cpu-low-throughput, throughput-collapse]
source_id: tuned
source_url: https://github.com/redhat-performance/tuned
source_license: GPL-2.0
license_verified: false
track: core
applicability:
  kernel: "RHEL9 / RHEL10 (tuned >=2.x)"
  hardware: x86_64
  software: tuned daemon must be active
tokens:
  abstract: 44
  digest: 460
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# tuned profiles in RHEL9 vs RHEL10: which sysctls change and why

## Abstract
tuned applies performance-relevant kernel parameters, CPU governor, IRQ
affinity, and disk scheduler settings as named profiles. If RHEL9 and RHEL10
benchmark hosts apply different profiles, or the same profile name sets
different values across releases, the sysctl configuration is a confound that
must be checked before attributing performance differences to kernel or
scheduler changes.

## Digest
**Checking active profile and what it sets:**
```bash
tuned-adm active              # active profile name
tuned-adm profile_info        # sysctls and settings this profile applies
tuned-adm recommend           # what tuned recommends for this hardware
```

**Key profiles for throughput benchmarks:**

*throughput-performance* — the standard choice for server benchmarks:
- CPU governor: `performance` (no frequency scaling)
- Disables transparent huge pages or sets to `madvise`
- `vm.dirty_ratio=40`, `vm.dirty_background_ratio=10`
- `net.core.busy_read=0` (no busy polling)
- `kernel.sched_min_granularity_ns` tuned for throughput
- IRQ affinity: allows all CPUs

*network-throughput* — extends throughput-performance for network workloads:
- Increases `net.core.rmem_max`, `net.core.wmem_max` to 16MB
- Sets `net.core.netdev_budget=600` (higher softirq budget)
- Enables RPS/RFS with broad CPU mask

*latency-performance* — for latency-sensitive workloads:
- CPU governor: `performance`
- Disables C6 sleep states
- `kernel.sched_min_granularity_ns` smaller (faster preemption)

**RHEL9 vs RHEL10 profile differences** [distiller-added — verify on actual hosts]:
Profile implementations may differ between tuned versions shipped with each
RHEL release. The same profile name may set different values. To get a
definitive diff:
```bash
# On RHEL9 host
tuned-adm profile_info throughput-performance > rhel9_profile.txt

# On RHEL10 host
tuned-adm profile_info throughput-performance > rhel10_profile.txt

diff rhel9_profile.txt rhel10_profile.txt
```

**Critical sysctls to verify match on both hosts:**
```bash
sysctl net.core.rmem_max net.core.wmem_max
sysctl net.ipv4.tcp_rmem net.ipv4.tcp_wmem
sysctl net.core.netdev_budget
sysctl vm.dirty_ratio vm.dirty_background_ratio
sysctl kernel.sched_min_granularity_ns
cat /sys/kernel/mm/transparent_hugepage/enabled
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```
If any of these differ between RHEL9 and RHEL10, standardize before attributing
performance differences to the kernel.

**Standardizing for benchmarks.** Set the same profile on both hosts:
```bash
tuned-adm profile throughput-performance
# or for network benchmarks:
tuned-adm profile network-throughput
```
Then verify with `sysctl -a` that values converge. For cross-release
reproducibility, consider listing the specific sysctls in the benchmark
`run.json` or a setup script rather than relying on profile names.

## Pointers
- tuned source: https://github.com/redhat-performance/tuned
- Related units: `rhel9-rhel10-kernel-delta`, `eevdf-vs-cfs`, `irq-softirq-napi`
- Annex raw: none
