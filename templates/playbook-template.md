---
# (frontmatter per schema; type: playbook; tags MUST include symptom tags)
---

# {title, phrased as the problem: e.g. "Throughput collapse under connection scaling from userspace lock contention"}

## Symptom signature
<!-- Observable facts only, as an investigator would first see them.
e.g. "QPS plateaus then degrades past N connections; CPU not saturated;
sys% low; run-queue short; off-CPU time in futex_wait." -->

## Environment
<!-- What the original case ran on, and how far the playbook generalizes. -->

## Investigation chain
<!-- The heart of the unit. Numbered steps, each:
1. **Hypothesis** considered
2. **Measurement** taken (exact tool + invocation)
3. **Observation** and how it was interpreted (including dead ends —
   dead ends teach the discrimination step)
Keep the original's reasoning order; this is process knowledge. -->

## Root cause
<!-- Mechanism, one paragraph. -->

## Fix and verification
<!-- What changed, and the measurement that confirmed it (before/after
numbers with units). -->

## Generalization
<!-- The reusable rule: "when you see {signature}, check {X} before {Y}
because {mechanism}". This line also feeds indexes/SYMPTOMS.md. -->

## Pointers
- Original write-up: {source_url}
