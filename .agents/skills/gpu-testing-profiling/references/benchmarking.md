# Reproducible benchmarking

## Preparation

1. Record the [baseline contract](performance-baseline.md) and authorization.
   The affected functional gate must pass before accepting timings.
2. Fix the workload, resolution, assets/SPIR-V and hashes, ABI, compiler,
   cache, options, screen/refresh rate, loading, power, and thermal conditions.
   Do not change DVFS/thermal controls. Missing observations do not establish
   thermal stability; report that limitation.
3. Before running, define the primary metric/unit, limit, warmup, repetitions,
   and functional/non-degradation tolerances. For an initial comparison,
   use 5 alternating A/B pairs in AB/BA order with fresh processes. This is a
   minimum screening protocol, not a statistical guarantee. If insufficient,
   the result is inconclusive.
4. Keep cold-load separate from steady-state. Warming up before measuring
   `bc_level` invalidates the cold-load question; do not clear global caches.

## Existing workloads and commands

Use binaries already prepared by build-validation; do not copy a glibc ELF
into Bionic. Use an isolated target directory and a local ICD with a verified
hash, with `timeout` syntax and remote termination behavior confirmed:

```sh
PT_WP_MS=400 timeout -k 3s 60s ./workload-perf ./libvulkan_panfrost.so
PT_TESS_MS=300 PT_TESS_AB=default timeout -k 3s 60s ./tess-perf ./libvulkan_panfrost.so
BCPERF_SIZE=256 timeout -k 3s 60s ./bc-perf ./libvulkan_panfrost.so BC4_UNORM
timeout -k 3s 20s ./submit-stress ./libvulkan_panfrost.so 100 1 5
```

These are plans for a **small first run**, not executed/qualified benchmarks.
Run one line at a time. An expired deadline is an execution FAIL and invalidates
the sample; it is never a performance timing. `PT_*_MS` limits per-configuration
windows, not setup, the total number of configurations, or waits. Do not
increase limits automatically. For prolonged workloads, obtain new cumulative
limits, cooldown, and thermal criteria; repeat the same bounded workload
without an infinite loop.

| Workload / source | Output and semantics | Acceptance and limits |
|---|---|---|
| [workload-perf.c](../../../../device/workload-perf.c) | `BENCH workload_perf case=... ms=... us_op=... fps=... ops=... frames=...`; wall time for an already recorded command buffer plus submit/fence and callback. `bc_level` measures create-image through upload-fence, separately from `device_ms` | `WORKLOAD_PERF_FAILS=0`, `PASS workload_perf`, exit 0; require image checks. `gs_pass/ref`, `strip_gs/strip_ref`, `xfb_*`, `msaa_*`, `tex_*` are not on-screen FPS |
| [tess-perf.c](../../../../device/tess-perf.c) | `BENCH tess_perf opt=... gs=... L=... draws=... patches=... ms=... us_draw=... frames=...`; resubmission/fence, not recording cost | `TESS_PERF_FAILS=0`, `PASS tess_perf`, exit 0, no MISMATCH/LEVEL_IGNORED/LOWMEM; preserve checks per configuration |
| [bc-perf.c](../../../../device/bc-perf.c) | `PERF fmt=... mem_KiB=... upload_gpu_ms=... upload_wall_ms=... A_ms=... wallA=...`; upload uses the best of 3, passes use the median of 5 after warmup | `RESULT DONE`, exit 0, required format not SKIP. This is not the complete BC1-BC7 contract; use BC functional tests for correctness |
| [submit_stress.c](../../../../tests/dxvk/vulkan/submit_stress/submit_stress.c) | Limits by submissions and seconds; prints actual submissions in `SUBMIT_STRESS PASS`, `RESULT PASS` | Do not divide the requested maximum by elapsed time after a time-limited stop. External timing includes init/teardown; label throughput end-to-end |
| PanProbe `swapchain_lifecycle` | `BENCH present`/results and the Android presentation image | Time inside `vkQueuePresentKHR` is not GPU execution time or the interval between displayed frames |

By default, tess-perf performs an A/B of **historical** knobs within one run.
`PT_TESS_AB=default` avoids that unintended change; use fresh processes to
compare two revisions. Do not assume historical knobs retain their meaning
in the current series without source confirmation.

## Timestamp and compute/bandwidth blockers

Before `workload-perf` or `bc-perf`, confirm `timestampValidBits > 0` for the
queue family actually used and `timestampPeriod > 0` for the target ICD,
using an identified properties dump. Both create queries without safely
skipping when that capability is unavailable. If unknown/absent, do not run
these programs and mark BLOCKED; `ts_pair` measures query/readback overhead,
not GPU duration. Timestamp differences must respect valid bits, wrap, and
availability. `bc-perf` subtracts values directly: use a short capture with
no wrap confirmed, or treat GPU timing as invalid. Do not turn zero into a
valid result.

[Compute smoke](functional-testing.md) does not measure compute throughput.
No qualified pure-compute Moto benchmark or isolated buffer-copy bandwidth
workload was identified. Those gates remain BLOCKED until a suitable existing
workload/setup is approved; do not create a duplicate benchmark.
BC `upload_wall_ms` includes decoding/emulation and is not memory bandwidth.
Estimate bytes/time only when transferred bytes and the isolated interval
are established, labeling it effective throughput, not peak DRAM bandwidth.

## Collection and analysis

Preserve raw output per run, exit status, command/environment, and counts.
Do not aggregate different cases, variants, best-of-3, and median-of-5 results
as independent samples. Internal `frames` within a window do not replace runs.

For individual frames, record the unit, clock, and measurement point; calculate
median/p95/p99 with a declared percentile method, min/max, and dispersion.
Without individual samples, do not derive p95/p99 from average FPS.
Aggregate FPS = `1000 / mean(frame_ms)`, not the mean of instantaneous FPS.
`workload_perf ms` is mean offscreen frame time; `1000/ms` is the equivalent
for that workload, not presented FPS. Use
[optimization comparison](optimization-validation.md) to reach a conclusion.
