---
id: rhel9-rhel10-kernel-delta
title: "RHEL9 vs RHEL10 kernel delta: scheduler, MM, mitigations, and default tuning"
type: reference
domain: kernel
tags: [high-sys-cpu, low-cpu-low-throughput, p99-tail, memory-pressure, throughput-collapse]
source_id: kernel-docs
source_url: https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/
source_license: CC-BY-SA-4.0
license_verified: false
track: core
applicability:
  kernel: "RHEL9 (kernel-5.14-based) vs RHEL10 (kernel-6.12-based)"
  hardware: x86_64
  software: any
tokens:
  abstract: 55
  digest: 580
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# RHEL9 vs RHEL10 kernel delta: scheduler, MM, mitigations, and default tuning

## Abstract
RHEL9 (kernel 5.14) and RHEL10 (kernel 6.12) differ by ~7 major kernel
versions, carrying several default-behavior changes that affect benchmark
results independent of hardware. This unit is the review-agent checklist: when
a RHEL9/RHEL10 comparison shows unexpected metric differences, work through
these four areas before attributing the delta to the benchmark configuration
or hardware.

## Digest
When RHEL9 and RHEL10 benchmark results differ, four kernel-level changes are
the first-order explanations. Check them in this order — they are ordered by
how often they explain observed deltas in general-purpose compute benchmarks.

**1. Scheduler: CFS (RHEL9) → EEVDF (RHEL10)**
RHEL9 runs CFS; RHEL10 runs EEVDF (merged upstream in 6.6). EEVDF changes
wakeup latency distribution and preemption frequency. Diagnostic:
- `pidstat -w 1 30` — involuntary context switch rate differs → scheduler signal
- `sar -q 1 30` — run-queue depth distribution changes
- `perf sched latency --sort max` — wakeup latency tail

See unit `eevdf-vs-cfs` for the mechanism and full diagnostic commands.

**2. Memory management: MGLRU (RHEL10 default) vs inactive/active LRU (RHEL9)**
RHEL10 enables MGLRU by default. RHEL9 backported it in 9.3 but leaves it off.
Under memory pressure, MGLRU changes which pages are evicted, reducing refault
rates for mixed hot/cold workloads. Diagnostic:
- `cat /sys/kernel/mm/lru_gen/enabled` — non-zero on RHEL10, zero on RHEL9 (unless manually enabled)
- `grep workingset_refault /proc/vmstat` — compare between hosts
- `sar -B 1 30` — pgsteal rate differences

To isolate: enable MGLRU on the RHEL9 host (`echo y > /sys/kernel/mm/lru_gen/enabled`) and re-run.

See unit `mglru-page-reclaim` for details.

**3. Spectre-class mitigations: generation change**
RHEL9 on older hardware uses retpoline + legacy IBRS (expensive on pre-eIBRS
CPUs). RHEL10 on newer hardware (Cascade Lake+) gets eIBRS which costs far
less. On the same hardware, the mitigation set may differ due to kernel version
and microcode. Diagnostic:
```bash
# On both hosts
cat /sys/devices/system/cpu/vulnerabilities/spectre_v2
cat /proc/cpuinfo | grep bugs
```
If RHEL10 reports `eibrs` where RHEL9 reported `retpoline,ibrs`, expect lower
`%sys` CPU overhead on RHEL10 for syscall-heavy workloads. If same mitigation,
this is not the cause.

**4. Default tuning: tuned profile and sysctl differences**
RHEL9 and RHEL10 may apply different default tuned profiles. Verify:
```bash
tuned-adm active           # active profile on each host
tuned-adm profile_info     # what sysctls the profile sets
sysctl -a | grep -E 'vm\.|net\.core\.|kernel\.sched' > sysctls.txt
```
Key sysctls that affect benchmark results: `vm.dirty_ratio`,
`net.core.rmem_max`, `net.core.wmem_max`, `net.core.netdev_budget`,
`kernel.sched_min_granularity_ns`. If profiles differ, standardize to
`throughput-performance` on both hosts for a clean comparison.

**Review agent checklist for RHEL9 vs RHEL10 tickets:**

1. Confirm kernel versions: `uname -r` on both hosts (check ticket custom_fields or run data)
2. Check scheduler: `cat /sys/kernel/debug/sched/features | grep EEVDF`
3. Check MGLRU: `cat /sys/kernel/mm/lru_gen/enabled`
4. Check mitigations: `cat /sys/devices/system/cpu/vulnerabilities/spectre_v2`
5. Check tuned profile: `tuned-adm active`
6. Diff `%sys` between the two runs — if RHEL10 shows more `%sys` despite fewer features, attribution order: scheduler overhead, mitigation overhead, new background kernel threads
7. Diff `%soft` per CPU — if one CPU saturated on one run → IRQ imbalance, not OS version effect

**Important:** None of these differences automatically mean one OS is "better."
Each change has workload-specific tradeoffs. Report the measured delta, identify
the mechanism, and recommend a follow-up measurement to confirm causation.
Do not attribute a result to "EEVDF" without showing the involuntary context
switch or wakeup latency data that supports it.

## Pointers
- Related units: `eevdf-vs-cfs`, `mglru-page-reclaim`, `kernel-spectre-mitigations`, `tuned-profiles-rhel`
- RHEL release notes: https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/
- Annex raw: none
