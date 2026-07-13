---
id: cpu-frequency-turbo
title: "CPU frequency, turbo boost, C-states, and AVX frequency licensing"
type: concept
domain: hardware
tags: [throughput-collapse, low-ipc]
source_id: gregg-sysperf-book
source_url: https://www.brendangregg.com/systems-performance-2nd-edition-book.html
source_license: proprietary
license_verified: false
track: digest
applicability:
  kernel: any
  hardware: "x86_64 Intel (AVX licensing specific to Intel); AMD has similar turbo mechanisms without AVX licensing"
  software: "compute-heavy workloads; AVX/AVX-512 users; any workload sensitive to frequency variance"
tokens:
  abstract: 44
  digest: 470
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# CPU frequency, turbo boost, C-states, and AVX frequency licensing

## Abstract
CPU cores do not run at a fixed frequency. Turbo boost raises frequency above
the base rate when thermal budget allows; AVX-512 workloads on Intel force a
frequency reduction across all cores; deep C-states add exit latency penalties.
When throughput degrades after minutes at full load, or when a compute workload
runs slower than expected, frequency behavior is a first-order check before
blaming software.

## Digest
**turbostat — the primary tool:**
```bash
turbostat --quiet --show Busy,Bzy_MHz,IRQ,CPU%c1,CPU%c6,PkgWatt sleep 10
```
Key columns:
- `Bzy_MHz` — actual MHz when not idle. Compare to base and advertised turbo.
- `CPU%c6` — fraction of time in deep C6 sleep state.
- `PkgWatt` — package power draw; approaching TDP signals thermal throttle risk.

**Turbo boost mechanics.** All-core turbo is lower than single-core turbo.
A 3.0 GHz base CPU may single-core turbo to 3.8 GHz but all-core turbo to only
3.2 GHz. When all cores are busy (full benchmark load), the sustained frequency
is the all-core turbo, not the advertised peak. Verify:
```bash
# See current frequency per core
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq
```

**Intel AVX frequency licensing** [distiller-added, Intel-specific]:
Running AVX-256 or AVX-512 instructions reduces the allowed frequency for the
*entire package* to a lower "AVX license" tier. This means:
- A benchmark that vectorizes with AVX-512 may run at 2.4 GHz all-core instead
  of 3.2 GHz.
- The first AVX instruction in a period triggers the frequency drop; the CPU
  takes ~milliseconds to recover after AVX stops.
- Detection: `turbostat` shows `Bzy_MHz` drop coinciding with AVX-heavy code.
- Relevant for: BLAS/LAPACK, FFT, some network drivers (checksum offload can
  trigger it), memcpy in some versions.

**C-state exit latency.** Modern CPUs enter idle states to save power between
events. C6 (deepest common state) has an exit latency of ~100–200µs on Intel
Xeon. For latency-sensitive workloads (sub-millisecond response time), this
adds tail latency:
```bash
# Disable C6 for a session (not persistent)
cpupower idle-set -d 3   # disable state 3 (typically C6)

# Or use the latency-performance tuned profile which does this automatically
tuned-adm profile latency-performance
```

**P-state governor:**
```bash
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
# performance → always maximum frequency (no turbo savings, minimum latency)
# powersave → frequency scales with load (potential latency variance)
```
RHEL tuned profiles: `throughput-performance` sets `performance` governor;
`balanced` (default on many installs) may use `powersave`.

**RHEL9 vs RHEL10 difference.** Governor defaults and C-state management may
differ between tuned versions. Verify `turbostat` `Bzy_MHz` is similar on both
hosts during the benchmark — if one shows consistently lower MHz, check the
governor and C-state configuration before attributing performance differences to
the kernel scheduler.

## Pointers
- `turbostat` man page; Intel TurboBoost documentation
- Related units: `thermal-throttling`, `tuned-profiles-rhel`, `rhel9-rhel10-kernel-delta`
- Annex raw: none
