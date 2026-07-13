---
id: gpu-occupancy-utilization
title: "GPU occupancy, SM utilization, and the GPU utilization number trap"
type: concept
domain: gpu-ml
tags: [gpu-underutilized]
source_id: cuda-best-practices
source_url: https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/
source_license: nvidia-proprietary
license_verified: false
track: pointer
applicability:
  kernel: any
  hardware: "NVIDIA GPU; specifics vary by architecture (Ampere/Hopper/Blackwell)"
  software: "CUDA, PyTorch, vLLM, any GPU workload"
tokens:
  abstract: 47
  digest: 470
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# GPU occupancy, SM utilization, and the GPU utilization number trap

## Abstract
`nvidia-smi`'s GPU utilization reports the fraction of time at least one kernel
was active — it says nothing about efficiency. A GPU running one underperforming
kernel at 10% compute throughput shows 100% utilization. SM occupancy (active
warps / maximum warps) and roofline model position (compute-bound vs memory-
bandwidth-bound) are the meaningful metrics for diagnosing why GPU work is
slower than expected.

## Digest
**The `nvidia-smi` util trap.** `nvidia-smi --query-gpu=utilization.gpu` returns
the percentage of the last sample window during which at least one CUDA kernel
was running. It does not measure SM utilization, warp efficiency, memory
bandwidth, or compute throughput. A kernel that launches and immediately stalls
on a cache miss shows 100% util while delivering near-zero useful work.

**Polling with dmon:**
```bash
# 1-second polling: clock, temperature, power, utilization, memory
nvidia-smi dmon -s pucmt -d 1

# Columns: pwr (W), gtemp (C), sm% (SM util), mem% (mem util),
#          enc% (encoder), dec% (decoder), mclk (memory clock), pclk (proc clock)
```
`sm%` is closer to true compute utilization: fraction of time SMs were running
at least one warp. `mem%` is memory controller utilization.

**SM Occupancy.** The fraction of maximum theoretical warps that are resident
on SMs simultaneously. Low occupancy (< 50%) means the GPU cannot hide memory
latency — when a warp stalls on a memory load, no other warp is available to
run. Low occupancy causes include:
- High register usage per thread (limits warps per SM)
- Large shared memory allocation per block
- Small launch configuration (few blocks, few threads per block)

Measured with Nsight Compute:
```bash
ncu --metrics sm__warps_active.avg.pct_of_peak_sustained_active ./kernel
```

**Roofline model for diagnosis.** Plot the workload's arithmetic intensity
(FLOPs / bytes transferred to/from HBM). If it is below the roofline knee
(HBM bandwidth limit), the workload is memory-bandwidth-bound — adding compute
won't help. If above the knee, it is compute-bound.
- LLM decode: memory-bandwidth-bound by design (KV cache reads dominate)
- LLM prefill: compute-bound (matrix multiplications)
- Low SM util during decode is expected and correct, not a problem

**When "GPU underutilized" is a real problem:**
- During prefill: low SM util means compute isn't saturating (check batch size,
  tensor parallelism, kernel launch overhead)
- Gaps between kernels in Nsight Systems timeline: CPU is not feeding the GPU
  fast enough (tokenization, Python overhead, data pipeline)
- Consistent sub-30% SM util during training: check data loader bottleneck

**Nsight Systems timeline** (the right tool for full-system diagnosis):
```bash
nsys profile --trace=cuda,nvtx,osrt --output=profile.qdrep ./vllm_server
nsys-ui profile.qdrep    # open in GUI
```
Look for: gaps between CUDA kernels (CPU-bound), H2D/D2H transfer overlap with
compute (or lack thereof), kernel duration distribution.

## Pointers
- CUDA C++ Best Practices Guide: https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/
- Nsight Compute user guide: https://docs.nvidia.com/nsight-compute/
- Related units: `vllm-continuous-batching`, `nccl-topology-collective`, `gpu-pcie-host-device`
- Annex raw: none
