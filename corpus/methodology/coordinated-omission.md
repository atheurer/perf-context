---
id: coordinated-omission
title: Coordinated omission in latency measurement
type: concept
domain: methodology
tags: [latency, percentiles, benchmarking, load-generation, p99-tail]
source_id: tene-coordinated-omission
source_url: https://github.com/HdrHistogram/HdrHistogram
source_license: BSD-2-Clause (HdrHistogram); concept from Tene talks
license_verified: false
track: core
applicability:
  kernel: any
  hardware: any
  software: any
tokens:
  abstract: 45
  digest: 420
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# Coordinated omission in latency measurement

## Abstract
A measurement error where a load generator that waits for responses before
sending the next request silently drops exactly the samples that occur
during slow periods, making reported p99/p999 latency wildly optimistic.
Check for it before trusting any latency benchmark, yours or a vendor's.

## Digest
Closed-loop load generators (send, wait for response, send next) coordinate
with the system under test: when the system stalls, the generator stops
issuing requests, so the stall is recorded as one slow sample instead of
the hundreds of requests that *would* have arrived during it in production.
The resulting percentile distribution can understate tail latency by orders
of magnitude while p50 looks fine. Real clients are open-loop — they arrive
regardless of how the last request went — so closed-loop percentiles answer
a question nobody asked.

Detection rules:
- If the tool's request timing depends on response completion (default wrk,
  many DB benchmarks, naive scripts), assume coordinated omission unless
  corrected.
- Compare intended vs actual request timestamps; gaps clustered after slow
  responses are the signature.
- A suspiciously smooth percentile curve that cliff-drops only at max is
  another tell.

Remedies:
- Use an open-loop or corrected generator: wrk2 (constant throughput with
  latency measured from *intended* send time), fio's rate-based modes,
  or HdrHistogram's correction APIs (record with expected interval) when
  you can't fix the generator.
- Report latency-vs-throughput curves, not a single load point; measure at
  fixed arrival rates below saturation.
- In service-time vs response-time terms: closed-loop tools measure
  service time; users experience response time (queueing included). State
  which one a number is.

Traps:
- HdrHistogram-style correction is an estimate; prefer a genuinely
  open-loop generator when the tail matters.
- Fully open-loop at a rate above capacity diverges (unbounded queue);
  sweep rates and report the knee.
- Averaged latencies and time-bucketed means hide the same tail this
  error hides; always work in percentiles from full histograms.

## Pointers
- Gil Tene, "How NOT to Measure Latency" (talk; multiple recordings) —
  worked examples and generator demos.
- HdrHistogram README and `recordValueWithExpectedInterval` docs.
- Related units: latency-percentiles (TBD), open-vs-closed-loop-benchmarking (TBD).
