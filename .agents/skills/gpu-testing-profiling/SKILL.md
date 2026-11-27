---
name: gpu-testing-profiling
description: "Use for PanVK/Kraid functional tests, regressions, stability, benchmarks, profiling, and comparative optimization evaluation on the Moto G86 Mali-G615 MC2, using Android/Bionic or glibc in a chroot. Does not validate builds/packages or generalize results to other GPUs."
---

# GPU testing and profiling

Turn the task into a bounded experiment: **test, measure, collect, analyze,
compare, and validate**. Do not turn a list of tools into a support promise.

## Scope and responsibilities

- Active validation matrix: Moto G86, Mali-G615 MC2, MT6878, `PAN_ARCH=11`,
  Kbase CSF. Android 16 is the documentation target, not a current device
  reading. Confirm model, GPU, SoC, OS, kernel, UAPI, and context before running.
- Mesa/Kraid: use inputs from [sources.lock](../../../sources.lock), not a
  moving branch. Record effective compiler selection; glibc is opt-in and
  is not equivalent to Android/Bionic. Here, glibc means userspace running
  in a chroot on the Android handset.
- [panvk-build-validation](../panvk-build-validation/SKILL.md) validates
  provenance, compilation, ELF, and packaging. This skill receives that
  handoff and validates **behavior, stability, and performance** through
  separate gates. Do not rebuild merely to write documentation.
- [panfrost-panvk](../panfrost-panvk/SKILL.md): Vulkan implementation;
  [kraid-compiler](../kraid-compiler/SKILL.md): compiler;
  [mali-kernel-platform](../mali-kernel-platform/SKILL.md): UAPI, CSF,
  DMA-BUF, memory, and platform. Hand off the cause with evidence; this skill
  does not authorize changes to those components.

The [existing profile](../../../profiles/g615-v11-csf.json) describes the
Poco X6 Pro MC6, not the Moto MC2. Its name does not establish the Moto's
hardware, mask, permissions, or ABI. Do not change it or copy its values
to fill evidence gaps.

## Choose the procedure

| Task | Required procedure |
|---|---|
| Smoke, compute, rendering, memory, synchronization, AHB/WSI, regressions | [Functional testing](references/functional-testing.md) |
| Prepare a workload, run a benchmark, collect timings/FPS | [Benchmarking](references/benchmarking.md) |
| Collect CPU/GPU/memory/CSF data and confirm availability | [Profiling](references/profiling.md) |
| Interpret data and distinguish causes | [Bottlenecks](references/bottleneck-analysis.md) |
| Compare a candidate with its baseline and approve or reject a gain | [Optimizations](references/optimization-validation.md) |
| Identity, history, report format | [Baseline](references/performance-baseline.md) |

## Required workflow

1. State the question, measurable criterion, and workload. Read only the
   corresponding procedure and baseline contract.
2. Reuse existing evidence with its original identity and limitations.
   If it answers the question, do not repeat tests. Finding a document is
   static evidence; its reported result remains historical until reproduced.
3. Check the build/package handoff and the identity of the ICD actually loaded.
   Different binaries, unitless data, or unknown contexts do not establish a
   comparison. `driverInfo` or enumeration alone does not establish the hash.
4. Before hardware execution, obtain authorization for the device, test,
   installation, paths, limits, and collection. Preparing commands, reading
   local logs, and analyzing synthetic data do not require physical benchmarks.
5. Run only the necessary case in an isolated process/path. Record complete
   output, exit status, counts, checks, and the effective limit. Stop new
   submissions on timeout, fault, device-lost, corruption, a critical thermal
   condition, or loss of responsiveness.
6. Compare with a compatible baseline and record the first causal failure.
   A hypothesis requires an additional discriminating measurement, not
   changing several flags until the result looks better.
7. Deliver a report in the [defined format](references/performance-baseline.md),
   separating facts, observations, hypotheses, and unknowns.

## Approval rules

Use `PASS`, `FAIL`, `BLOCKED`, and `NOT EXECUTED` for each gate: provenance,
build/ELF/package (handoff), functionality, stability, performance, and audit.
A missing prerequisite is `BLOCKED`; an optional execution not performed is
`NOT EXECUTED`. `SKIP`, `NotSupported`, warnings, and partial logs are not a
functional PASS. An information field marked `UNKNOWN` is not a success status.

Do not approve an optimization without a reproducible comparison, documented
variability, no functional regression, and predefined non-degradation
criteria. One fast frame, fewer instructions, or offscreen microbenchmark FPS
does not demonstrate a presentation or gaming improvement.

Do not write clocks, governors, firmware, or debugfs controls, change SELinux,
clear logcat, or reboot/reset to test a hypothesis. Terminate only the
authorized isolated process using its confirmed PID. Do not install a
profiler, use root, or upload logs automatically. Inaccessible interfaces
remain unavailable; do not invent counters.

## Skill status

The [offline audit](references/operational-audit.md) records the inventory,
exercises, and generation gates. Documentation approval does not create a
Moto performance baseline or qualify hardware. Final approval belongs to the user.
