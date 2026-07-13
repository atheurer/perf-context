---
id: vllm-kv-cache-paged-attention
title: "vLLM paged attention and KV cache: mechanics, capacity, and preemption"
type: concept
domain: gpu-ml
tags: [kv-cache-pressure, tpot-high, gpu-oom]
source_id: vllm
source_url: https://github.com/vllm-project/vllm
source_license: Apache-2.0
license_verified: false
track: core
applicability:
  kernel: any
  hardware: "NVIDIA GPU with >=16GB VRAM for 7B models; Ampere+ for BF16"
  software: "vLLM >=0.4; PagedAttention concept applies to SGLang and other runtimes"
tokens:
  abstract: 49
  digest: 510
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# vLLM paged attention and KV cache: mechanics, capacity, and preemption

## Abstract
vLLM's paged attention stores KV cache in fixed-size memory blocks (pages)
rather than contiguous per-sequence buffers. This eliminates internal
fragmentation and enables sharing across requests with common prefixes. When
KV cache fills, vLLM preempts existing sequences (evicting their KV to CPU
memory or recomputing). The preemption rate is the key metric for KV cache
pressure — high preemption causes TPOT spikes and throughput collapse.

## Digest
**Why KV cache matters.** Attention computes queries against keys and values
from all previous tokens. These KV tensors must be stored for every token in
every active sequence. Memory requirement grows linearly with sequence length
and number of concurrent requests. On a 40GB A100 running a 7B model (model
weights ~14GB BF16): ~26GB available for KV cache. At 2KB per token (typical
7B BF16), this supports roughly 13M tokens across all sequences simultaneously.

**Paged memory mechanics.** KV cache is divided into blocks of fixed size
(default 16 tokens per block). Sequences are allocated blocks on demand, like
OS virtual memory pages. This eliminates the "reserve max_seq_len for every
sequence" fragmentation of naive implementations. Multiple sequences can share
blocks for identical prefix tokens (prefix caching).

**KV cache capacity calculation** [distiller-added]:
```
kv_bytes_per_token = 2 × num_layers × num_kv_heads × head_dim × dtype_bytes × 2 (K+V)
available_cache_bytes = gpu_memory - model_weight_bytes - runtime_overhead
max_tokens = available_cache_bytes / kv_bytes_per_token
```
`--gpu-memory-utilization` (default 0.9) controls how much GPU memory vLLM
reserves for KV cache. Reduce for stability; increase to fit more concurrent
sequences.

**Preemption: detection and impact.**
```bash
# vLLM metrics (prometheus endpoint at :8000/metrics)
vllm_num_preemptions_total          # total preemption events
vllm_gpu_cache_usage_perc           # 0.0-1.0 KV cache fill fraction
vllm_num_running_seqs               # active sequences
vllm_num_waiting_seqs               # queued sequences waiting for cache
```
When `vllm_gpu_cache_usage_perc` approaches 1.0, preemption frequency rises.
Preemption either swaps KV to CPU (slow: PCIe bandwidth limited) or
recomputes (very slow: must re-run prefill). Both cause TPOT to spike for
affected sequences. The signature: TPOT is stable then suddenly jumps by 2–5×,
correlating with `vllm_num_preemptions_total` incrementing.

**Tuning to reduce preemption:**
- Reduce `max_num_seqs` (limit concurrent sequences)
- Reduce `max_model_len` (shorter sequences = less KV per request)
- Increase `--gpu-memory-utilization` (more cache headroom)
- Enable prefix caching to share blocks across common prefixes:
  `--enable-prefix-caching`

**TPOT vs preemption attribution.** If TPOT degrades under load, first check
`vllm_gpu_cache_usage_perc`. If it is below 0.7, preemption is not the cause —
look at decode batch size and memory bandwidth. If above 0.9 with preemptions
incrementing, KV cache pressure is confirmed.

## Pointers
- vLLM paged attention paper: https://arxiv.org/abs/2309.06180
- vLLM docs: https://docs.vllm.ai/en/latest/design/kernel/paged_attention.html
- Related units: `vllm-continuous-batching`, `vllm-prefix-cache`, `gpu-occupancy-utilization`
- Annex raw: none
