---
name: perf-context-router
description: Navigate the perf-context knowledge repository during performance investigation, characterization, benchmarking, or optimization tasks on Linux systems and GPU/ML inference stacks. Use this skill whenever you are diagnosing a performance symptom (high latency, low throughput, CPU/memory/IO/network saturation or the lack of it, tail latency, GPU underutilization), choosing measurement tools, interpreting profiler or counter output, or planning a tuning change — even if you believe you already know the answer, check the symptom index first for playbooks that may shortcut or correct your approach.
---

# perf-context router

This repo stores performance-engineering knowledge as small digests behind
two indexes. Your job is to load the minimum that changes your next action.

## Protocol

1. **Classify your task.**
   - Live investigation (you have a symptom) → step 2.
   - Planning/characterization/learning (no symptom yet) → step 3.
2. **Symptom entry:** grep `indexes/SYMPTOMS.md` for your observables
   (use the symptom tag vocabulary listed at the top of that file; also try
   raw terms like "sys%", "p99", "IPC", "run queue", "preemption").
   Each row maps symptom → candidate hypotheses → first measurements →
   unit ids. Load the referenced **playbooks first** — they encode
   hypothesis ordering, which is the expensive thing to get wrong.
3. **Topic entry:** read `indexes/INDEX.md` (abstracts only), then the
   relevant `corpus/<domain>/INDEX.md`. Select units by abstract.
4. **Load digests** for selected units. Before loading, sum the
   `digest_tokens` values against your remaining budget; if over budget,
   rank by how directly the abstract addresses your current hypothesis.
5. **Escalate to pointers only when load-bearing.** Fetch the full source
   only if the digest's interpretation rules are insufficient for the
   decision in front of you. Note in your scratchpad why you escalated.
6. **Check `applicability` before acting** on any digest: kernel version,
   hardware generation, software version. A mismatched digest is
   disinformation. Prefer units with `quality: eval-validated`.

## Budget rules

- A routing pass (indexes + abstracts) should cost <2k tokens.
- Loading more than 5 digests before taking your first measurement is a
  smell: you are reading instead of measuring. Measure, then return here
  with a sharper symptom.
- Record which units you loaded and whether they changed your actions;
  emit this in your run log (feeds Phase-4 corpus attribution).

## When the corpus is silent

If neither index covers your symptom, say so explicitly in your log
(feeds gap analysis), fall back to first-principles USE-method triage
(corpus/methodology/use-method*), and proceed with standard tooling.
Do not fabricate corpus citations.
