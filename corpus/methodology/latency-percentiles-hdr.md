---
id: latency-percentiles-hdr
title: "Latency percentiles: interpretation, HDR histogram, and tail behavior"
type: concept
domain: methodology
tags: [p99-tail]
source_id: tene-coordinated-omission
source_url: https://github.com/HdrHistogram/HdrHistogram
source_license: BSD-2-Clause
license_verified: false
track: core
applicability:
  kernel: any
  hardware: any
  software: any benchmarking scenario
tokens:
  abstract: 44
  digest: 430
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# Latency percentiles: interpretation, HDR histogram, and tail behavior

## Abstract
p99 latency means 99% of requests completed faster; 1% were slower. Means
and averages hide tail behavior that users experience. HDR Histogram captures
latency across a high dynamic range without losing precision at the tail. When
analyzing benchmark results, always ask: what is the load, what is the
percentile, what is the sample size — without all three, the number is
uninterpretable.

## Digest
**Percentile semantics.** p50 is the median — half of requests faster, half
slower. p99 = 99th percentile. p99.9 = 999th of 1000. For a user-facing
service at 1000 rps, p99.9 means one request per second is slower than this
threshold. p99 means 10 requests per second exceed it. The tail matters more
at higher request rates.

**Why means hide problems.** A bimodal distribution — 99% of requests at 1ms,
1% at 500ms — has a mean of ~6ms. Neither the fast mode nor the slow mode is
visible in the mean. This is why latency results should always be reported as
percentile distributions, not averages.

**HDR Histogram.** Standard histograms require pre-specified bucket boundaries.
HdrHistogram uses log-linear buckets to cover a dynamic range (e.g., 1µs to
10s) with configurable precision (e.g., 3 significant digits). Tools: wrk2,
uperf (with histogram mode), HdrHistogram Java/C/Go libraries.

**Reading uperf histogram output.** uperf in crucible reports latency
percentiles when `histogram: true` is set in the run.json. The CDM will have
latency percentile data under the `latency` metric. When comparing RHEL9 vs
RHEL10:
- p50 difference → median service time changed (scheduler/memory overhead)
- p99 difference without p50 difference → tail event (IRQ, GC, page fault)
- Both differ proportionally → systematic overhead on all requests

**Percentile vs throughput graphs.** For stream tests, throughput (GB/s or
Mpps) is the primary metric. For latency-sensitive RPC tests, plot latency vs
offered load: the knee of the latency curve (where latency begins growing
nonlinearly) is the sustainable throughput limit. See `queueing-theory-basics`
for why the knee occurs at ~70–80% utilization.

**Reporting requirements.** A latency number is meaningless without:
1. The percentile (p99? p50? mean?)
2. The load at which it was measured (offered RPS or throughput)
3. The sample size (10 samples of p99 is much noisier than 10,000)
4. Whether coordinated omission affects it (see `coordinated-omission`)

**Comparing two runs.** When RHEL9 shows p99=2ms and RHEL10 shows p99=3ms:
- First verify load was identical (`perf stat` syscall rate, throughput numbers)
- Check sample count — small samples make p99 noisy
- Look at the distribution shape, not just the percentile value
- A 50% p99 increase with identical p50 suggests tail events (IRQ, scheduler
  jitter) rather than systematic overhead

## Pointers
- HdrHistogram: https://github.com/HdrHistogram/HdrHistogram
- Gil Tene, "How NOT to Measure Latency" (talk)
- Related units: `coordinated-omission`, `queueing-theory-basics`, `open-vs-closed-loop-load`
- Annex raw: none
