---
id: hypothesis-driven-investigation
title: "Hypothesis-driven performance investigation: the drill-down loop"
type: concept
domain: methodology
tags: [high-sys-cpu, p99-tail, throughput-collapse, low-cpu-low-throughput]
source_id: gregg-site
source_url: https://www.brendangregg.com/methodology.html
source_license: all-rights-reserved
license_verified: false
track: digest
applicability:
  kernel: any
  hardware: any
  software: any
tokens:
  abstract: 46
  digest: 440
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# Hypothesis-driven performance investigation: the drill-down loop

## Abstract
Effective performance investigation follows a loop: observe symptom, form
hypotheses, select a measurement that discriminates between them, interpret
result, eliminate or confirm. Skipping straight to "it's the network" or
tuning before measuring wastes time and frequently blames the wrong layer.
This unit describes the loop and the failure modes that short-circuit it.

## Digest
**The loop:**
1. **Observe** — collect the symptom precisely: what metric, what value, under
   what load, on what system. "Slow" is not a symptom. "p99 latency 45ms at
   1000 rps, p50 is 3ms" is.
2. **Hypothesize** — list candidate root causes, ordered by prior probability.
   For a RHEL9→RHEL10 throughput difference: scheduler change, mitigation
   change, MM change, network stack change, tuning difference. Not "the kernel."
3. **Select a discriminating measurement** — a measurement that will produce
   *different* output depending on which hypothesis is true. "More metrics"
   is not a strategy. "pidstat -w to check if involuntary context switch rate
   changed" is.
4. **Measure** — collect the data without interpreting it yet.
5. **Eliminate or confirm** — does the data match what the hypothesis predicts?
   If yes, confirm mechanism. If no, eliminate and move to the next hypothesis.
6. **Explain the mechanism** — a root cause is not confirmed until you can
   explain *how* the mechanism produces the observed symptom. "EEVDF" is not an
   explanation. "EEVDF preempts more aggressively, increasing involuntary
   context switch rate by 3×, adding scheduler overhead that reduces effective
   CPU time for the uperf process by 8%" is.

**The "what changed?" question.** When comparing two systems or two OS versions,
the scope of the investigation is bounded by what differs between them. List
all variables that changed (OS version, kernel version, tuned profile, hardware
if any). Check each one — do not assume only one changed.

**Document eliminations.** Negative evidence is evidence. If you checked
mitigation strings and they are identical on both hosts, that rules out
mitigation cost as the explanation. Record this; it prevents re-investigating
the same dead end and builds the case for the actual root cause.

**Misinterpretation traps:**
- *Correlation is not causation*: RHEL10 has higher `%sys` AND has EEVDF does
  not mean EEVDF caused the higher `%sys`. Test by checking scheduler-specific
  metrics (context switch rate, wakeup latency).
- *The first explanation is often wrong*: the visible symptom (high `%sys`) may
  have multiple causes; the most obvious one is not always the dominant one.
- *"No data" is not "no problem"*: if sar/mpstat data was not collected during
  the run, do not assume the metrics were normal. Note the gap and recommend
  collecting them in follow-up runs.

**For a two-run OS comparison specifically:**
1. Confirm both runs used the same benchmark configuration.
2. Run USE checklist on both (see `use-method`).
3. Route symptom deltas through SYMPTOMS.md.
4. Load at most 5 candidate units; check applicability.
5. For each: state the mechanism, cite the metric values, confirm or eliminate.
6. If no measurement discriminates: report observed-but-unexplained with the
   specific follow-up measurement that would resolve it.

## Pointers
- Brendan Gregg methodology page: https://www.brendangregg.com/methodology.html
- Related units: `use-method`, `rhel9-rhel10-kernel-delta`, `coordinated-omission`
- Annex raw: none
