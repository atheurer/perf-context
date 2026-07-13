---
id: vllm-continuous-batching
title: "vLLM continuous batching: prefill vs decode phases, TTFT and TPOT"
type: concept
domain: gpu-ml
tags: [ttft-high, tpot-high, gpu-underutilized]
source_id: vllm
source_url: https://docs.vllm.ai/en/latest/design/arch_overview.html
source_license: Apache-2.0
license_verified: false
track: core
applicability:
  kernel: any
  hardware: "NVIDIA GPU; Ampere+ for BF16 efficiency"
  software: "vLLM >=0.4"
tokens:
  abstract: 48
  digest: 490
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# vLLM continuous batching: prefill vs decode phases, TTFT and TPOT

## Abstract
LLM inference has two computationally distinct phases: prefill (processing the
full prompt in one parallel pass — compute-bound) and decode (generating one
token per step by attending over KV cache — memory-bandwidth-bound). Continuous
batching interleaves new requests with ongoing decoding, improving GPU
utilization. The TTFT/TPOT SLO tradeoff is the central scheduling problem.

## Digest
**Phase distinction.** During prefill, all prompt tokens are processed in one
forward pass. The computation is O(seq_len²) in attention, making long prompts
expensive and making prefill compute-bound (arithmetic intensity high). During
decode, a single new token attends over all KV cache entries for that sequence.
The computation is O(seq_len) but memory-bound: the bottleneck is reading the
KV cache from HBM, not FLOPs.

**TTFT = Time To First Token.** Measured from request arrival to first generated
token. Dominated by: (1) time spent in queue waiting for a free slot; (2) the
prefill computation itself. Long prompts cause long TTFT. Under high load, TTFT
grows as prefill compute contends with decode batch requests.

**TPOT = Time Per Output Token.** Measured between consecutive generated tokens.
Dominated by: (1) decode batch size (more sequences = more KV to load from HBM);
(2) HBM bandwidth; (3) KV cache preemption overhead. TPOT is relatively
constant at low load; it grows with batch size and KV cache pressure.

**Continuous batching mechanics.** Orca-style continuous batching: new requests
join the batch at iteration boundaries without waiting for current requests to
finish. The scheduler decides each iteration which sequences to prefill vs
decode. Default vLLM policy: prioritize prefill for waiting requests, then fill
remaining slots with decode steps.

**Key metrics for diagnosis:**
```bash
# From vLLM prometheus metrics
vllm_request_queue_size              # waiting requests → high = TTFT will rise
vllm_num_running_seqs                # active decode sequences
vllm_request_prefill_time_seconds    # prefill latency histogram
vllm_request_decode_time_seconds     # decode latency histogram
vllm_gpu_cache_usage_perc            # KV cache utilization
```

**TTFT high, TPOT fine.** Likely cause: long prefill queue. Requests arrive
faster than prefill can process them. Fix: limit max prompt length, use chunked
prefill (see `vllm-chunked-prefill`), or scale prefill capacity.

**TPOT high, TTFT fine.** Likely cause: large decode batch (many concurrent
sequences loading KV cache simultaneously), KV cache pressure causing
preemption, or memory bandwidth saturation. Check `vllm_gpu_cache_usage_perc`
first.

**GPU utilization in decode.** `nvidia-smi` showing 60–70% GPU utilization
during decode is not a problem — decode is HBM bandwidth-bound by design. The
GPU compute units are underutilized while memory bandwidth is saturated. Do not
attempt to "improve" decode GPU utilization by adding more sequences unless
TPOT is acceptable at higher batch sizes.

## Pointers
- vLLM architecture overview: https://docs.vllm.ai/en/latest/design/arch_overview.html
- Orca continuous batching paper (reference): https://www.usenix.org/conference/osdi22/presentation/yu
- Related units: `vllm-kv-cache-paged-attention`, `vllm-chunked-prefill`, `vllm-prefix-cache`, `gpu-occupancy-utilization`
- Annex raw: none
