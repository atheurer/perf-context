# perf-context taxonomy

Domain directories under `corpus/`. Each will carry its own INDEX.md of
unit abstracts (generated in Phase 3). Subtopics below define distiller
tagging targets and harvest curation scope.

## methodology
Investigation method (USE, drill-down, off-CPU analysis, hypothesis
discipline); workload characterization; queueing theory, Little's Law,
utilization/latency curves; Amdahl/Gustafson; latency percentiles and
coordinated omission; benchmarking design, statistics, and measurement
bias; capacity planning; experiment design and A/B for systems.

## observability
perf (record/stat/c2c/mem/sched); eBPF: bcc, bpftrace, libbpf tools;
ftrace/tracepoints/kprobes/uprobes; flame graphs (CPU, off-CPU, diff);
PMU counters and Top-down Microarchitecture Analysis; VTune/uProf/likwid;
sysstat family and PCP; blktrace/biolatency; ss/ethtool/tcpdump for perf;
load generators (fio, stress-ng, netperf/iperf3, wrk) as measurement
instruments; GPU profilers cross-listed with gpu-ml.

## hardware
Cache hierarchy, TLB, page walks; NUMA topology and placement; memory
bandwidth vs latency, prefetchers; branch prediction, speculation, SMT;
coherence (MESI/MOESI), false sharing; core topologies and frequency
behavior (turbo, AVX licensing, C/P-states); PCIe topology, lanes,
switches, host bridges; NVMe internals; NIC offloads, DPDK, RDMA;
roofline modeling; per-architecture notes (Zen, Golden Cove+, Neoverse).

## kernel
Scheduler (EEVDF, and CFS as historical), run queues, wakeup paths,
affinity/isolation; memory management: page cache, reclaim/MGLRU, THP and
hugepages, folios, zone/NUMA balancing; cgroup v2 controllers and
throttling; IRQ handling, softirq, NAPI, busy polling; network stack path
(GRO/GSO, qdiscs, TCP behavior); block layer, io schedulers, io_uring;
locks: futex, spinlock evolution, RCU; syscall overhead, mitigations
(spectre-class) cost; tuned profiles and sysctl semantics.

## runtimes
JVM: GC selection/tuning, JIT warmup, JFR; Go: GC, scheduler, pprof,
execution tracer; Python: GIL, free-threading, perf integration;
compilers: -O levels, vectorization reports, PGO, LTO, BOLT; malloc
implementations (glibc, jemalloc, tcmalloc) and fragmentation.

## distributed
Tail latency at scale, hedging, retries/backoff/jitter, metastable
failure; load balancing and overload control; backpressure and queue
management; caching hierarchies and invalidation cost; consistent
hashing/sharding; capacity models and autoscaling; RPC/serialization
overhead; observability at fleet scale (RED/golden signals).

## gpu-ml
GPU execution model: occupancy, warps, memory coalescing, shared memory
bank conflicts; host-device transfer, pinned memory, streams and overlap;
Nsight Systems/Compute metric interpretation; roofline for GPUs; NCCL and
collective topology (rings/trees, NVLink vs PCIe vs network); LLM
inference: continuous batching, paged KV cache, prefix caching,
speculative decoding, quantization runtime tradeoffs, MoE serving and
expert locality; vLLM/SGLang internals and tuning surfaces; PyTorch
profiler and torch.compile; tokenization and host-side bottlenecks;
serving SLOs: TTFT/TPOT/goodput.
