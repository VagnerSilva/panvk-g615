# Operational bottleneck diagnosis

Follow this sequence: **observation -> falsifiable hypothesis -> single
variable -> metric/control -> prediction -> result -> conclusion**.
Use [profiling](profiling.md) for availability and
[benchmarking](benchmarking.md) for timing semantics.
Before analyzing performance, rule out functional failure, the wrong ICD,
timeouts, and incomplete logs. Do not try to optimize incorrect results.

| Observation | Hypothesis, not a confirmed cause | Collection and discriminating control | Handoff |
|---|---|---|---|
| Wall time increases, GPU timestamp remains similar | CPU recording, submit, waiting, or readback | Per-thread CPU plus recording/submit/wait timings for the same workload; instrumented versus uninstrumented capture. If wall time changes without a GPU difference and CPU work concentrates in submission, investigate that path; do not subtract incompatible clocks | PanVK; kernel only when a wait/ioctl is identified |
| Higher resolution increases GPU time | Fragment work, textures, bandwidth, or overdraw | Same workload/assets, change only resolution if supported; compare GPU/wall and content. Scaling alone does not distinguish ALU from memory; requires a qualified counter or traffic variant with equivalent work | PanVK/Kraid after discrimination |
| Slow BC upload | Decode/compile/transcode or transfer | BC `upload_wall_ms/upload_gpu_ms`, `bc_level/device_ms`; separate cold versus warm. Verify quality/readback and format. Faster warm timing suggests cache/compilation; does not establish DRAM saturation | PanVK/Kraid |
| RSS/heap rises and MemAvailable/SwapFree drops with long frames | Memory pressure/paging | `MEM`, `/proc`, frame times from the same window; repeat the same workload with initially healthy memory, without clearing caches/swap or killing other apps. If spikes persist without pressure, the hypothesis weakens | PanVK/mali-kernel-platform |
| `tex_bgra` performs worse than `tex_rgba` | Conversion/swizzle/cache/layout | Paired workload cases, identical conditions, functional checks; collect timestamps/counters if available. Format names do not establish bandwidth | PanVK/Kraid |
| Wait without completion | Fence/sync_file, queue dependency, fault, or an earlier error | First verify create/import/submit, valid/pending FD, signal/poll/readback, deadline, and context. Compare `sync_test --cross-queue` and the single-queue case; import failure before submission blocks completion | mali-kernel-platform/PanVK |
| Submissions/s drops with render-pass count | CPU recording/submission or GPU work in each batch | submit_stress: preserve actual count/limit, vary only rps with identical correctness checks; measure wall/CPU/waits. The microbenchmark includes waits; without a trace it does not provide firmware latency | PanVK; CSF with correlated logs |
| Fast offscreen, slow presentation | WSI, copying, compositor, pacing, v-sync | Compare only as a qualitative control; measure present and displayed intervals at the same resolution. Offscreen lacks the same WSI workload; refresh-limited FPS does not mean GPU saturation | PanVK/Android |
| Temperature/frequency changes accompany performance loss | Throttling/DVFS | Only qualified nodes/confirmed units; cooldown and alternating AB/BA. Without readings, report suspicion rather than asserting throttling | Platform |
| Fewer instructions/spills, unchanged frame time | Compiler optimization outside the critical path | Affected workload and unaffected control, timing comparison; compiler statistics are supporting evidence, not GPU measurements | Kraid |

## Memory: do not confuse indicators

Image `mem_KiB` is a Vulkan requirement; `heap_used_KiB` is budget/usage;
RSS/HWM is process memory; MemAvailable/SwapFree is system memory; bandwidth
would be bytes/s with established interval/traffic. Do not add these values
or relabel one as another. A 2008 ms spike with little free swap in a
historical log does not establish the cause on the current Moto.

## Synchronization: stop at the first causal gate

If the AHB image returns `VK_ERROR_INVALID_EXTERNAL_HANDLE` before release,
the correct record is: **FAIL import/metadata; release unexercised, BLOCKED;
performance BLOCKED**. Do not infer deadlock, a faulty fence, or a WSI fix.
Shell release PASS and app import FAIL are results from different contexts.
Without a new GPU workload/readback, a signaled sync_file does not establish
coherency.

## Limits on conclusions

If two explanations remain consistent with the evidence, report INCONCLUSIVE
and propose one additional test whose result would distinguish the hypotheses.
Do not automatically add knobs, workloads, or Mesa instrumentation as part
of analysis; preparing the change and obtaining approval is the specialist's
task. Do not generalize historical MC6/JM results or extrapolate a small
experiment to endurance/reset/recovery.
