---
id: queueing-theory-basics
title: "Queueing theory basics: utilization-latency curves, Little's Law, M/M/1"
type: concept
domain: methodology
tags: [p99-tail, low-cpu-low-throughput, run-queue-long, throughput-collapse]
source_id: brooker-blog
source_url: https://brooker.co.za/blog/
source_license: all-rights-reserved
license_verified: false
track: digest
applicability:
  kernel: any
  hardware: any
  software: any
tokens:
  abstract: 47
  digest: 450
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# Queueing theory basics: utilization-latency curves, Little's Law, M/M/1

## Abstract
Queueing theory explains why latency grows nonlinearly as utilization
approaches 100%, why bursts matter more than averages, and why "add more
capacity" often does not fix tail latency. The M/M/1 model is the analyst's
calibration tool: real systems are worse, but the model predicts the shape of
the curve and the location of the knee. These relationships apply to any
saturating resource — CPU, NIC, disk queue, thread pool.

## Digest
**M/M/1 response time.** For a single server with Poisson arrivals and
exponential service times:
```
R = S / (1 - U)
```
Where R = mean response time, S = mean service time, U = utilization (0–1).
At U=0.5: R = 2S (2× service time). At U=0.8: R = 5S. At U=0.9: R = 10S.
At U=0.99: R = 100S. The curve is convex — performance degrades slowly then
collapses. **The practical cliff is U ≈ 0.7–0.8** for systems with any variance
in service time or arrival rate; targeting 100% utilization guarantees bad
latency. [distiller-added: real systems with non-exponential service times
(M/G/1) are generally worse at the tail than M/M/1 predicts.]

**Little's Law.** N = X × R: the average number of requests in the system
equals throughput (X, completions/sec) times mean response time (R, seconds).
Use it to sanity-check measurements:
- If uperf reports 10 Gbps throughput with 1 connection and 16KB messages:
  X ≈ 10e9/8/16384 ≈ 76,000 completions/sec. If observed response time R ≈ 0.3ms,
  then N ≈ 76000 × 0.0003 ≈ 23 messages in flight. Does that match connection count?

**Why bursts destroy tail latency.** Even at 50% average utilization, a burst
of requests arriving close together creates a queue. The last arrival in the
burst waits for all previous ones to complete — p99 reflects the burst size,
not the average. This is why p99 can be 10× p50 at moderate utilization.

**Identifying queueing from metrics:**
```bash
# CPU run queue — are tasks waiting to run?
sar -q 1 30     # runq-sz > CPU count = queueing at the scheduler

# Disk queue
iostat -x 1 30  # aqu-sz > 1 = disk is queueing requests

# Network socket recv queue
ss -ti | grep Recv-Q   # non-zero Recv-Q = kernel buffer backlog
```

**The closed-loop vs open-loop distinction.** Benchmarks that wait for a
response before sending the next request (closed-loop) bound concurrency to 1
per thread, preventing queueing. They measure service time, not response time.
Real clients are open-loop — they arrive regardless of server state. See
`coordinated-omission` and `open-vs-closed-loop-load` for implications.

**Applying to RHEL9 vs RHEL10 comparisons.** If throughput is the same on
both but latency differs, check run-queue depth: higher `runq-sz` on one OS
means the scheduler is queueing tasks more — a sign of higher scheduling
overhead or different time-slice behavior. The queueing theory model predicts
that even a small increase in scheduler service time (S) produces
disproportionate latency growth at high utilization.

## Pointers
- Marc Brooker blog: https://brooker.co.za/blog/
- Related units: `coordinated-omission`, `open-vs-closed-loop-load`, `use-method`
- Annex raw: none
