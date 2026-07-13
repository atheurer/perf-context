# SYMPTOMS — inverted index (symptom → hypotheses → first measurements → units)

Primary entry point for live investigations. Unit-id columns are filled by
the Phase-3 indexer as corpus units land; hypothesis/measurement columns
are seeded now and refined from playbooks.

Symptom tag vocabulary (use in unit frontmatter `tags`):
`high-sys-cpu` `high-user-cpu` `low-cpu-low-throughput` `p99-tail`
`throughput-collapse` `run-queue-long` `iowait-high` `memory-pressure`
`swap-thrash` `numa-remote` `false-sharing` `lock-contention`
`irq-storm` `softirq-saturation` `packet-drops` `retransmits`
`cgroup-throttled` `low-ipc` `frontend-bound` `backend-bound`
`gpu-underutilized` `gpu-oom` `kv-cache-pressure` `ttft-high`
`tpot-high` `pcie-bound` `collective-slow` `gc-pause`

| Symptom signature | Likely hypotheses (ordered) | First measurements | Units |
|---|---|---|---|
| High sys% CPU, throughput flat | syscall-heavy path; lock contention in kernel; page faults; network stack cost | `perf top -g` kernel side; `pidstat -w`; `perf stat -e context-switches,page-faults` | `cgroup-cpu-throttling` `eevdf-vs-cfs` `irq-softirq-napi` `kernel-spectre-mitigations` `mpstat-sar-cpu-breakdown` `rhel9-rhel10-kernel-delta` `rps-rfs-xps-steering` |
| CPU not saturated, throughput plateaus with concurrency | userspace lock contention; single contended resource; connection/accept bottleneck; coordinated omission hiding it | off-CPU flame graph; `bpftrace` futex latency; check load generator methodology | `cgroup-cpu-throttling` `eevdf-vs-cfs` `mglru-page-reclaim` `rhel9-rhel10-kernel-delta` |
| p99 >> p50, p50 healthy | queueing at a burst-sensitive stage; GC/allocator pauses; timer/IRQ interference; NUMA remote hits on a subset | latency heatmap over time; `perf sched timehist`; GC logs; per-CPU breakdown | `coordinated-omission` `eevdf-vs-cfs` `rhel9-rhel10-kernel-delta` |
| Low IPC (<~0.5) on busy cores | memory-bound (LLC misses, DRAM bandwidth); false sharing; TLB pressure | TMA level 1 (`perf stat -M tma_...` / toplev); `perf c2c`; `perf stat -e dTLB-load-misses` | `kernel-spectre-mitigations` |
| One core pegged in softirq | IRQ steering imbalance; NAPI overload; RPS/RFS misconfig | `mpstat -P ALL`; `/proc/interrupts` deltas; `/proc/softirqs` | `irq-softirq-napi` `mpstat-sar-cpu-breakdown` `qdisc-ring-drops` `rps-rfs-xps-steering` |
| Throughput drops after minutes at steady load | thermal/frequency (AVX or turbo decay); page cache filled → reclaim; JIT deopt; KV cache fills → preemption | `turbostat`; `sar -B`; runtime-specific logs; vLLM preemption counters | `mglru-page-reclaim` `rhel9-rhel10-kernel-delta` |
| cgroup app slow, host idle | CPU quota throttling; memory.high reclaim pressure; io.max | `cpu.stat` nr_throttled; `memory.stat`; PSI (`/proc/pressure/*`, per-cgroup) | `cgroup-cpu-throttling` |
| GPU util low, model serving slow | input pipeline / tokenization CPU-bound; small batches (scheduler or load pattern); host-device transfer sync; CPU-GPU affinity across NUMA | Nsight Systems timeline (gaps between kernels); vLLM batch-size metrics; `nvidia-smi dmon`; check pinned memory | TBD |
| TTFT high, TPOT fine | prefill queueing; prefix cache misses; scheduler starvation of new requests | vLLM queue/scheduler metrics; request-size distribution; prefix cache hit rate | TBD |
| TPOT degrades under load | KV cache pressure → preemption/recompute; decode batch too large; memory bandwidth bound | vLLM preemption + cache usage metrics; Nsight Compute on decode kernels | TBD |
| Multi-GPU scaling poor | collective topology crossing host bridge/QPI; PCIe lane starvation; NCCL algo/protocol mismatch; stragglers | `nccl-tests` (all_reduce_perf) vs expected; `nvidia-smi topo -m`; NCCL_DEBUG=INFO topology dump | TBD |
| iowait high, disk "slow" | queue depth mismatch; io scheduler choice; write cache/barrier behavior; actually fine and CPU is waiting on sync semantics | `iostat -x` (aqu-sz, await vs svctm-era intuition traps); `biolatency`; fio baseline of raw device | `mpstat-sar-cpu-breakdown` |
| Packet drops / retransmits under load | ring buffer overflow; qdisc drops; rmem/wmem limits; incast | `ethtool -S` deltas; `ss -ti`; `nstat`; qdisc stats (`tc -s qdisc`) | `irq-softirq-napi` `qdisc-ring-drops` `rps-rfs-xps-steering` |

Maintenance rule: every playbook unit must either merge into an existing
row or add one. Rows with no units after Phase 2 are gap-analysis targets.
