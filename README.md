# perf-context

A knowledge repository for LLM agents doing performance and scale engineering:
investigation, characterization, and optimization of computing systems
(Linux systems performance + GPU/ML inference, day one).

The primary consumer is an agentic LLM (e.g. driven by `agentic-perf`) that
needs to behave like a top-tier performance engineer: form hypotheses from
symptoms, pick the right measurement tools, interpret data correctly, and know
the hardware/OS/runtime mechanisms underneath.

## Architecture: digests + pointers, progressive disclosure

This repo does **not** primarily store raw source material. It stores:

1. **Abstracts** (2-3 sentences per unit) — always cheap to scan
2. **Digests** (~500 tokens per unit) — original-prose distillations, loaded
   on demand
3. **Pointers** — canonical citations to the authoritative source (URL, repo
   path, book chapter) for when the agent needs full depth
4. **Playbooks** — normalized investigation runbooks (symptom → tools →
   hypothesis chain → root cause → fix → verification), distilled from real
   case studies
5. **Indexes** — a topic taxonomy index and a symptom→hypothesis inverted
   index (`indexes/SYMPTOMS.md`), which is the primary entry point for
   investigations

Raw fetched material, paywalled content, talk transcripts, and anything with
unclear redistribution rights lives in a **private annex** (separate repo,
see `annex/README.md`). The public core contains only original-expression
digests, pointers, and permissively-licensed source excerpts.

## Navigation protocol (for consuming agents)

1. Start from the task type:
   - Investigating a live problem → `indexes/SYMPTOMS.md`
   - Learning/planning/characterization → `indexes/INDEX.md` (per-domain
     indexes under `corpus/<domain>/INDEX.md`)
2. Scan abstracts only. Select candidate units.
3. Load digests for selected units (check `digest_tokens` in frontmatter
   against your context budget first).
4. Escalate to the pointer (fetch full source, or annex path if you have
   annex access) only when the digest is insufficient AND the source is
   load-bearing for your current hypothesis.
5. Respect `applicability` frontmatter — a digest describing CFS behavior is
   wrong advice on a 6.6+ EEVDF kernel; a CUDA digest for Ampere may not hold
   on Blackwell.

## Repo layout

```
registry/sources.yaml     Source registry: what to harvest, how, license, cadence
schemas/                  Frontmatter schema for corpus units
templates/                Digest and playbook formats
agents/                   Prompts for harvester / distiller / critic agents
skills/router/SKILL.md    The navigation skill given to consuming agents
indexes/                  INDEX.md (taxonomy) and SYMPTOMS.md (inverted index)
corpus/<domain>/          Distilled units, one markdown file each
annex/                    Stub explaining the private annex repo
PLAN.md                   Phased, agent-executable build plan
LICENSE-POLICY.md         Rules deciding public core vs annex vs pointer-only
```

## Status

Skeleton stage. `PLAN.md` Phase 0 is complete (this scaffold); Phase 1
(harvest) is ready to run against `registry/sources.yaml`.
