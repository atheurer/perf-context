---
id: nccl-topology-collective
title: "NCCL topology, collective algorithms, and multi-GPU scaling"
type: concept
domain: gpu-ml
tags: [collective-slow, pcie-bound]
source_id: nccl-docs
source_url: https://github.com/NVIDIA/nccl-tests
source_license: BSD-3-Clause
license_verified: false
track: core
applicability:
  kernel: any
  hardware: "NVIDIA multi-GPU; NVLink (intra-node) vs PCIe (cross-node or non-NVLink intra-node)"
  software: "NCCL >=2.x; PyTorch DDP, DeepSpeed, Megatron-LM"
tokens:
  abstract: 46
  digest: 480
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# NCCL topology, collective algorithms, and multi-GPU scaling

## Abstract
NCCL (NVIDIA Collective Communications Library) implements all-reduce, broadcast,
and other collective operations across GPUs. Performance depends critically on
the communication topology — NVLink GPUs on the same node can all-reduce at
hundreds of GB/s, while GPUs crossing a PCIe host bridge are 10–100× slower.
When multi-GPU training or inference scales poorly, topology crossing is the
first hypothesis to test.

## Digest
**Topology discovery:**
```bash
# Show GPU interconnect topology
nvidia-smi topo -m

# Output interpretation:
# NVL  = NVLink (fast, preferred)
# PXB  = PCIe crossbar (same PCIe switch, no CPU hop)
# PHB  = PCIe host bridge (crosses CPU/root complex, moderate)
# QPI/SYS = cross-socket via UPI/QPI (slow)
```
Any GPU pair connected via PHB or SYS for collective operations is a bottleneck.
HGX/DGX nodes with NVLink avoid this for intra-node collectives.

**Bandwidth expectations** [distiller-added]:
- NVLink A100 SXM: 600 GB/s bidirectional per GPU
- NVLink H100 SXM: 900 GB/s bidirectional per GPU
- PCIe Gen4 x16 per slot: ~64 GB/s bidirectional (shared across all PCIe traffic)
- Cross-socket (UPI): ~80–100 GB/s but shared across all cross-socket traffic

**Algorithm selection.** NCCL automatically selects ring, tree, or collnet
algorithm based on message size, topology, and number of ranks:
- Ring: bandwidth-optimal for large messages (>1MB); latency is O(N) hops
- Tree: latency-optimal for small messages; bandwidth is O(log N)
- NCCL_ALGO=RING or NCCL_ALGO=TREE to force

**Diagnosing slow collectives:**
```bash
# Baseline with nccl-tests
# all-reduce at various message sizes
./build/all_reduce_perf -b 8 -e 512M -f 2 -g <num_gpus>
# Compare bus bandwidth to theoretical maximum from topo -m

# NCCL debug output (verbose)
NCCL_DEBUG=INFO NCCL_DEBUG_SUBSYS=ALL ./your_workload 2>&1 | grep -E 'topology|algo|proto'
```
The `all_reduce_perf` bus bandwidth at large message sizes should approach
the bandwidth of the slowest link in the ring. If it is significantly below,
check: (1) PCIe topology crossing, (2) NCCL_SOCKET_IFNAME for inter-node
(ensure it uses the right NIC), (3) GPU affinity (P2P disabled?).

**P2P access check:**
```bash
NCCL_DEBUG=TRACE ... 2>&1 | grep P2P
# Look for "Could not enable P2P" which forces fallback through host memory
```
P2P access between GPU pairs requires same root complex or NVLink. Without P2P,
all transfers go GPU → pinned host memory → target GPU, cutting bandwidth and
adding CPU involvement.

**Cross-node NCCL.** For multi-node training, NCCL uses the network NIC for
inter-node communication. Performance depends on network bandwidth and latency:
InfiniBand HDR (200 Gbps) >> Ethernet (100 Gbps at best) >> Ethernet with
TCP/IP overhead. Ensure `NCCL_SOCKET_IFNAME` points to the correct RDMA or
high-bandwidth NIC.

**Scaling efficiency.** Plot throughput vs GPU count. Ideal linear scaling is
rare past 8 GPUs without NVLink. At 70–80% scaling efficiency at 8 GPUs, the
overhead is normal; below 50% indicates a topology or NCCL configuration issue.

## Pointers
- NCCL tests: https://github.com/NVIDIA/nccl-tests
- NCCL docs: https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/
- Related units: `gpu-pcie-host-device`, `gpu-occupancy-utilization`
- Annex raw: none
