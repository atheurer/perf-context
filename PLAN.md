# PLAN — building the perf-context corpus

Each phase lists tasks written to be executable by an LLM agent with web
fetch, git, and filesystem access. Human gates are marked **[HUMAN]**.

---

## Phase 0 — Scaffold (DONE)

- [x] Taxonomy (`indexes/INDEX.md`)
- [x] Unit frontmatter schema (`schemas/unit-frontmatter.yaml`)
- [x] License policy (`LICENSE-POLICY.md`)
- [x] Seed source registry (`registry/sources.yaml`)
- [x] Digest / playbook templates, agent prompts, router skill
- [ ] **[HUMAN]** Review taxonomy and license policy; adjust registry priorities

## Phase 1 — Harvest

Agent: `agents/harvester-prompt.md`. Input: `registry/sources.yaml`.

For each registry entry, in priority order (`priority: 1` first):

1. Verify the license claim in the registry against the source itself
   (LICENSE file, footer, copyright page). Update `license` and
   `license_verified: true|false` in the registry. If verification changes
   the `track`, apply `LICENSE-POLICY.md` rules.
2. Acquire content per `method`:
   - `git`: shallow-clone, extract only the paths in `paths:`, record commit
     SHA in provenance.
   - `fetch`: fetch pages listed in `urls:` (or crawl `crawl_root` to depth
     `crawl_depth`), convert to clean markdown.
   - `pointer`: do not fetch content; create a pointer-only stub unit.
3. Write raw material to the **annex** repo under
   `annex/raw/<source_id>/...` with a `provenance.yaml` (url, sha/etag,
   fetch date, license).
4. Append the harvested unit list to `registry/harvest-log.yaml`.

Acceptance: every priority-1 source harvested or marked blocked with reason;
zero raw content committed to the public core.

## Phase 2 — Distill

Agent: `agents/distiller-prompt.md`. Input: annex raw units. Output: corpus
units in `corpus/<domain>/`.

1. For each raw unit, produce a corpus unit per
   `templates/digest-template.md`: frontmatter, abstract, ~500-token digest,
   pointer block. Digests MUST be original prose (see LICENSE-POLICY §3).
2. If the source contains a worked investigation, ALSO extract a playbook
   unit per `templates/playbook-template.md` into the same domain dir with
   `type: playbook`.
3. Tag version/hardware applicability explicitly. When a mechanism has been
   superseded (CFS→EEVDF, pre/post io_uring, architecture generations), say
   so in the digest and set `applicability`.
4. Run the critic pass: `agents/critic-prompt.md` checks each digest against
   its raw source for unsupported claims, quantitative errors, and license
   policy violations. Digests failing the critic loop back to the distiller
   (max 2 iterations, then flag **[HUMAN]**).

Acceptance: every harvested unit has a corpus unit that passed critique;
spot-check 10% **[HUMAN]**.

## Phase 3 — Index

1. Regenerate `corpus/<domain>/INDEX.md` files: one line per unit
   (id — abstract — digest_tokens — type).
2. Regenerate top-level `indexes/INDEX.md` from domain indexes.
3. Extend `indexes/SYMPTOMS.md`: for every playbook and every digest with an
   observable failure signature, add/merge a symptom row linking to unit ids.
4. Validate: every unit reachable from an index; every index link resolves;
   frontmatter validates against schema (write `scripts/validate.py` if not
   present).

## Phase 4 — Evaluate (integrates with agentic-perf)

1. Build a task suite of injected pathologies, each a container/VM recipe +
   ground-truth root cause. Initial set (Linux): userspace spinlock
   contention, NUMA remote-memory placement, IRQ storm on one core, page
   cache thrash, TCP incast, cgroup CPU throttling. GPU/ML set: vLLM
   batch-size misconfiguration, KV-cache thrash/preemption, PCIe topology
   bottleneck (NCCL ring across host bridge), CPU-bound tokenization
   starving the GPU, unpinned host memory transfers.
2. Run the investigating agent A/B: with router skill + corpus vs. without.
   Score: root-cause identification, tool selection quality, tokens
   consumed, wall-clock, remediation validity.
3. Attribute corpus value: log which units were loaded in successful runs;
   prune or improve units that are loaded often but never help.
   (This is the same meaningful-vs-wasteful-progress question as the
   agentic-perf guardrail work — context loads are budget spends.)

## Phase 5 — Continuous ingestion

1. Watchers on registry entries with `cadence != once`: RSS/atom for blogs,
   release tags for kernel/vLLM/CUDA docs, conference cycles (P99 CONF,
   SREcon, LPC, KernelRecipes, FOSDEM, GTC).
2. On change: re-harvest → re-distill → critic → re-index. Bump
   `last_verified` on unchanged units annually; digests older than 24 months
   in fast-moving domains (gpu-ml, kernel) get forced re-verification.
3. Quarterly **[HUMAN]** review of eval scores and prune list.

---

## Budget guidance for agent runs

- Phase 1: mostly I/O; cheap. Parallelize per source.
- Phase 2 is the token sink. Budget roughly (raw_tokens × 1.3) per unit for
  distill+critique. Prioritize: methodology > playbook-bearing case studies >
  tool docs > reference material.
- Do not distill reference-manual-class sources (Intel SDM, CUDA C++
  Programming Guide) wholesale. Distill only the chapters the taxonomy
  needs; leave the rest as pointers.
