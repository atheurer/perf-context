---
id: kernel-spectre-mitigations
title: "Spectre-class mitigation costs: retpoline, eIBRS, IBPB overhead"
type: concept
domain: kernel
tags: [high-sys-cpu, low-ipc]
source_id: kernel-docs
source_url: https://www.kernel.org/doc/html/latest/admin-guide/hw-vuln/spectre.html
source_license: GPL-2.0
license_verified: false
track: core
applicability:
  kernel: "all; mitigation defaults vary significantly by kernel generation and CPU microcode version"
  hardware: "x86_64 Intel/AMD; overhead is CPU-generation-dependent (pre-eIBRS vs eIBRS capable)"
  software: "syscall-heavy workloads most affected; pure compute less affected"
tokens:
  abstract: 53
  digest: 520
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# Spectre-class mitigation costs: retpoline, eIBRS, IBPB overhead

## Abstract
Spectre-class CPU mitigations add overhead to every kernel entry and indirect
branch. The mitigation set active depends on both the kernel version and CPU
microcode. RHEL9 on older hardware may use the expensive legacy IBRS path;
RHEL10 on eIBRS-capable CPUs uses the cheaper enhanced variant. If comparing
RHEL9 and RHEL10 shows higher `%sys` on one OS, mitigation generation is a
candidate cause — check before attributing the difference to scheduler changes.

## Digest
**Mitigation taxonomy** (each defends a different attack vector):

| Mitigation | What it does | Cost |
|---|---|---|
| Retpoline | Replaces indirect branches with a non-speculating trampoline | Low on modern CPUs; moderate on older |
| Legacy IBRS | Suppresses indirect branch speculation on kernel entry/exit | High — serializes every syscall |
| Enhanced IBRS (eIBRS) | Hardware-level protection, no per-syscall barrier needed | Low |
| IBPB | Flushes branch predictor on context switch | Moderate — paid at every task switch |
| STIBP | Prevents SMT sibling speculation leakage | Low when applied per-CPU |

**Which is active:**
```bash
# Summary per vulnerability
cat /sys/devices/system/cpu/vulnerabilities/spectre_v2

# Example RHEL9 output on Broadwell (pre-eIBRS): "Mitigation: Retpoline, IBPB: conditional, IBRS_FW"
# Example RHEL10 output on Ice Lake (eIBRS): "Mitigation: Enhanced / Automatic IBRS; IBPB: conditional"
```
The presence of `IBRS_FW` (firmware IBRS, triggered in kernel) on RHEL9 where
RHEL10 shows `Enhanced IBRS` is the expensive-vs-cheap split. Legacy IBRS on a
pre-eIBRS CPU can cost 10–30% on syscall-heavy workloads. [distiller-added]

**Detecting mitigation overhead:**
```bash
# Syscall rate — is the workload syscall-heavy?
perf stat -e syscalls:sys_enter -a sleep 10

# IPC comparison with mitigations (lab only — never on production)
# Boot with mitigations=off, compare %sys and throughput
# Normal: cannot disable on production; use as calibration only

# Cross-host: same workload, same hardware, different RHEL version
# Higher %sys on one OS at same syscall rate → mitigation cost difference
```

**RHEL9 vs RHEL10 on the same hardware.** On Cascade Lake and newer (eIBRS
capable), both RHEL9 and RHEL10 should select eIBRS, so mitigation cost should
be similar. On Skylake-era hardware, RHEL9 may fall back to legacy IBRS path
while RHEL10 (with newer kernel and microcode expectations) may also. Check the
vulnerability file output on both hosts — if it's the same string, mitigations
are not the explanation for `%sys` differences.

**In AWS.** c5n.18xlarge uses Skylake-based Intel Xeon Platinum 8124M. eIBRS
was added in Cascade Lake; Skylake-based instances may use the retpoline+IBRS
path on both RHEL9 and RHEL10. Verify by reading the vulnerability file inside
the instance, not from instance type alone.

**When mitigations are the cause.** If `%sys` is elevated and syscall rate is
high, and mitigation strings differ between RHEL9 and RHEL10, this is the
explanation. The fix is not to disable mitigations but to understand the delta:
report it as "mitigation generation difference accounts for N% of the %sys
increase" and recommend testing on eIBRS-capable hardware for the clean
comparison.

## Pointers
- Kernel doc: `Documentation/admin-guide/hw-vuln/spectre.rst`
- LWN "Meltdown and Spectre": https://lwn.net/Articles/741266/
- Related units: `rhel9-rhel10-kernel-delta`, `mpstat-sar-cpu-breakdown`
- Annex raw: none
