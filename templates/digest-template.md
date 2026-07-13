---
# (frontmatter per schemas/unit-frontmatter.yaml)
---

# {title}

## Abstract
<!-- 2-3 sentences. This is ALL a routing agent sees before deciding to load
the digest, so it must state: what mechanism/tool/method this covers, and
when an investigator would need it. No throat-clearing. -->

## Digest
<!-- ~500 tokens (hard ceiling 800). Original prose. Optimize for an agent
mid-investigation, not a student:

- Lead with the operational takeaway (how to use / when it applies /
  what the numbers mean), then the mechanism.
- Concrete invocations and flags are high-value: `perf c2c record`,
  `bpftrace -e '...'`, VLLM_* env vars, sysctls.
- Quantitative anchors with era/hardware caveats: orders of magnitude,
  crossover points, default values.
- Interpretation rules: "IPC below ~0.5 on this class of core suggests
  memory-bound; confirm with TMA level 1 before touching code."
- Explicit failure modes and misinterpretation traps.
- If superseded or version-sensitive, say so in the first paragraph. -->

## Pointers
<!-- Canonical escalation path when the digest isn't enough. -->
- Source: {source_url} — {which section/chapter, why escalate}
- Related units: {ids}
- Annex raw copy: {annex_raw or "none"}
