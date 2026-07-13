---
id: vllm-prefix-cache
title: "vLLM prefix caching: hit rate, when it helps, and memory tradeoffs"
type: concept
domain: gpu-ml
tags: [ttft-high, kv-cache-pressure]
source_id: vllm
source_url: https://docs.vllm.ai/en/latest/automatic_prefix_caching.html
source_license: Apache-2.0
license_verified: false
track: core
applicability:
  kernel: any
  hardware: "NVIDIA GPU"
  software: "vLLM >=0.4 (basic prefix caching); SGLang has RadixAttention as reference implementation"
tokens:
  abstract: 44
  digest: 420
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# vLLM prefix caching: hit rate, when it helps, and memory tradeoffs

## Abstract
Prefix caching reuses KV cache blocks computed for prompt prefixes that are
identical across requests. When multiple requests share a system prompt or chat
history, the KV computation for shared tokens is done once and served from cache
on subsequent requests. This reduces TTFT and GPU compute load. The tradeoff is
cache memory that could otherwise serve more concurrent sequences.

## Digest
**Enable:**
```bash
vllm serve <model> --enable-prefix-caching
```
Enabled by default in vLLM v1 (>=0.6); opt-in in earlier versions.

**How it works.** Requests with identical leading tokens share KV cache blocks.
The shared blocks are reference-counted and evicted only when all referencing
requests complete and new blocks are needed. On a cache hit, the prefill for
shared tokens is skipped — the server returns the cached KV directly to the
attention kernel.

**When it helps significantly:**
- Fixed system prompt of >500 tokens reused across all requests
- Multi-turn chat where each turn prepends all previous turns
- RAG patterns with a large shared context prepended to different queries
- Batch inference on the same document with different questions

**When it does not help:**
- Diverse prompts with no common prefix
- Short contexts (<100 tokens) — cache blocks are small, overhead matters
- High request rate with diverse users (cache thrashes before reuse)

**Metrics:**
```bash
# Hit rate (prometheus)
vllm_cpu_prefix_cache_hit_rate    # CPU cache (if offloaded)
vllm_gpu_prefix_cache_hit_rate    # GPU cache hit rate; target > 0.3 for benefit

# Per-request
# Look for "prefix cache hit" in vLLM logs with --log-level=DEBUG
```
A GPU hit rate below 0.1 with prefix caching enabled means the workload has
insufficient shared prefixes — disable prefix caching to recover the memory for
the decode KV cache.

**Memory tradeoff.** Cached blocks are "locked" while any request references
them. Under high load, a large prefix cache competes with the KV cache needed
for active decode sequences. If `vllm_gpu_cache_usage_perc` is consistently
high and preemptions are rising after enabling prefix caching, the cache is
hurting more than helping. Disable or reduce its scope.

**SGLang RadixAttention.** SGLang's RadixAttention generalizes prefix caching
to a radix trie of shared KV subtrees, enabling sharing beyond exact prefixes.
It is the reference implementation of this idea and typically achieves higher
hit rates on multi-turn workloads than vLLM's block-aligned approach.

## Pointers
- vLLM automatic prefix caching docs: https://docs.vllm.ai/en/latest/automatic_prefix_caching.html
- Related units: `vllm-kv-cache-paged-attention`, `vllm-continuous-batching`
- Annex raw: none
