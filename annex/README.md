# Private annex (stub)

The annex is a **separate private repo** (suggested: `perf-context-annex`),
not a subdirectory here — keeping it out of this repo's history entirely is
what makes the core safely publishable.

Layout in the annex repo:

```
raw/<source_id>/           harvested raw material
raw/<source_id>/provenance.yaml
transcripts/<event>/       talk transcripts
personal/                  personally-licensed material (books, LWN sub)
```

Wiring: agents that need annex access receive its path via an environment
variable or config (e.g. `PERF_CONTEXT_ANNEX=/path/to/perf-context-annex`).
Corpus units reference annex material only via the `annex_raw` frontmatter
field; the router skill treats a missing annex as "pointer-only mode" and
escalates to the public `source_url` instead.

Rules: see LICENSE-POLICY.md §4. Nothing in `annex/` in this repo except
this README.
