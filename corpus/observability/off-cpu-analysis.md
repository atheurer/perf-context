---
id: off-cpu-analysis
title: "Off-CPU analysis: why tasks sleep, block, and how to profile it"
type: tool
domain: observability
tags: [lock-contention, iowait-high, p99-tail, low-cpu-low-throughput]
source_id: gregg-site
source_url: https://www.brendangregg.com/offcpuanalysis.html
source_license: all-rights-reserved
license_verified: false
track: digest
applicability:
  kernel: ">=4.9 (BPF stable); BCC tools required"
  hardware: any
  software: any multi-threaded application
tokens:
  abstract: 48
  digest: 490
quality: seed
created: 2026-07-13
last_verified: 2026-07-13
annex_raw: none
---

# Off-CPU analysis: why tasks sleep, block, and how to profile it

## Abstract
CPU flame graphs show only on-CPU time — they miss everything a task spends
sleeping, blocking on I/O, or waiting for locks. Off-CPU analysis profiles
blocked time using BPF tracing of scheduler switches. When a workload has low
CPU utilization but poor throughput or high latency, off-CPU profiling is the
next tool after the USE checklist: it answers "what are threads waiting for?"

## Digest
**The gap CPU profiling leaves.** A thread blocked waiting for a mutex, an I/O
completion, or a network response does not appear in `perf record` samples.
CPU utilization of 20% with 80% throughput deficit means 80% of time is spent
off-CPU — entirely invisible to on-CPU sampling. Off-CPU analysis traces
scheduler `sched_switch` events to measure time spent in each blocked state,
producing a flame graph where width = total blocked time by call stack.

**BCC offcputime:**
```bash
# Kernel + user stacks, trace for 30 seconds, all threads
offcputime -K -U 30 > offcpu.stacks

# Filter to a specific PID
offcputime -p <pid> 30 > offcpu.stacks

# Generate flame graph
flamegraph.pl --color=io --title="Off-CPU" < offcpu.stacks > offcpu.svg
```
`-K` captures kernel stacks, `-U` user stacks. Without `-U`, only kernel
stacks are shown — sufficient for identifying the blocking syscall but not the
application call site.

**Reading the output.** Stack frames at the top of off-CPU stacks are the
*reason* for blocking:
- `futex_wait` / `do_futex` → mutex/condition variable contention
- `schedule` → voluntary yield (sleep, wait on pipe/socket)
- `io_schedule` / `blk_mq_make_request` → blocked on disk I/O
- `tcp_recvmsg` / `sock_recvmsg` → blocked waiting for network data
- `schedule_timeout` → sleeping in a poll/select loop

**wakeuptime.** Pairs a sleeping thread with the stack that woke it:
```bash
wakeuptime -p <pid> 30     # who woke this process and from what code path?
```
Useful when a thread wakes late — the waker's stack shows where the delay
was introduced.

**Minimum duration filter.** To focus on significant blocks only:
```bash
offcputime -m 1000 30      # only show blocks >1ms
```
This eliminates voluntary short sleeps (scheduler housekeeping) and highlights
latency-relevant blocking.

**Common patterns for network benchmarks (uperf):**
- Client side blocking in `tcp_recvmsg` is normal for stream tests — it means
  the client is waiting for data, which is expected.
- *Abnormal*: client blocking in `futex_wait` means userspace lock contention
  in the benchmark process itself — check thread count vs available CPUs.
- *Abnormal*: both client and server blocking in `io_schedule` suggests
  unexpected disk I/O (logging, swap, core dump path).

**Prerequisites and gotchas:**
```bash
# Check BPF support
uname -r    # >=4.9 required
ls /usr/share/bcc/tools/offcputime  # BCC must be installed

# kptr_restrict may hide kernel symbols
sysctl kernel.kptr_restrict   # 0 = full symbols; 1 = partial
echo 0 > /proc/sys/kernel/kptr_restrict   # temporary, as root
```

## Pointers
- Brendan Gregg, Off-CPU Analysis: https://www.brendangregg.com/offcpuanalysis.html
- BCC offcputime: https://github.com/iovisor/bcc/blob/master/tools/offcputime_example.txt
- Related units: `use-method`, `futex-lock-contention`, `bcc-offcpu-tools`
- Annex raw: none
