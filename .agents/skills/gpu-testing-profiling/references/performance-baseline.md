# Baseline, inventory, and history

## Record per execution

Reuse the project's approved evidence directory; create a new subdirectory
per campaign/run without overwriting records. No physical Moto baseline
directory was created during this generation. Do not copy logs to third parties.

Record:

```text
run_id, UTC, evidence_class (STATIC_CONFIRMED / HISTORICAL_REPORT /
  REPRODUCED / HYPOTHESIS / UNKNOWN / SYNTHETIC)
question, expected_result, acceptance_thresholds
device_model, GPU, core_count, SoC, PAN_ARCH, frontend
OS/build, kernel, Kbase_UAPI, firmware (UNKNOWN if not known), page_size
ABI/libc, shell/app_UID/chroot, loader, application/test_revision
Mesa_commit/version, project_revision, patchSeriesId, applied_variant/manifest
Kraid_revision/source_identity, effective_compiler_selection, env/debug_flags
ICD_path, loaded_ICD_SHA256, Build_ID, package_hash, build_handoff
workload/case, executable/asset/SPIR-V_hashes, resolution, ops/frames
command/env, deadline/grace, warmup, cache_policy, repetitions/order
screen/refresh, charging/battery_state, thermal/frequency observations
metrics (value/unit/source/clock/interval/availability), raw_samples
exit_status, expected/executed_checks, mismatches/skips, logs/capture_paths
aggregation/percentile_method, variability, exclusions/reasons
gates, verdict, limitations, next_discriminating_test
```

Minimize personal data: do not record serials/accounts/data from other apps
in the report. A local device identifier is sufficient to pair the unit.
Do not replace `UNKNOWN` with a value from the MC6 profile. Build ID is
supporting evidence; SHA-256 of the loaded bytes is mandatory for comparison.
A computed input series does not establish application: receive the build
manifest/log. Integrated Kraid does not establish selection in every stage.

Gates: provenance, build/ELF/package (handoff), functionality, stability,
performance, audit; statuses `PASS/FAIL/BLOCKED/NOT EXECUTED`. Historical
evidence preserves its original result; the current campaign gate is separate.

## Comparability

Compare only runs with complete identity and context for the question.
An MC6 baseline, vendor ICD, different ABI, different flags/cache/resolution,
or versions with multiple deltas are references, not an A/B of a Moto
optimization. Unknown optional information may limit the conclusion; an
unknown indispensable prerequisite blocks the gate. Do not compare ms/draw
with ms/frame, end-to-end timing with GPU timestamps, or a best sample with
a median without explanation.

## Reusable inventory (static, during this skill's generation)

| Resource | Use and evidence boundary |
|---|---|
| [tests/README.md](../../../../tests/README.md) and sources cited in [functional testing](functional-testing.md) | Compute magic 10/10, rendering/readback, AHB, loader, synchronization, and diagnostic modes; procedures, not executions performed during this generation |
| [workload-perf.c](../../../../device/workload-perf.c), [tess-perf.c](../../../../device/tess-perf.c), [bc-perf.c](../../../../device/bc-perf.c), [submit_stress.c](../../../../tests/dxvk/vulkan/submit_stress/submit_stress.c) | Reuse workloads, knobs/limits, and output; confirm semantics and timestamp prerequisite gates; do not duplicate scripts |
| [PanProbe CMakeLists.txt](../../../../apps/panvk-test/app/src/main/cpp/CMakeLists.txt) and [MainActivity.kt](../../../../apps/panvk-test/app/src/main/java/dev/zenithblue/panvktest/MainActivity.kt) | Integrate benchmarks and tests, with 300s BC/240s workload-tess/120s submit timeouts; these are not automatically approved limits. CMake has a local header default that does not establish the pin; hand off preparation |
| [run-vk-cts-subset.sh](../../../../scripts/dxvk/run-vk-cts-subset.sh) | duchamp/Alpine runner, not a Moto/glibc runner; do not bypass the guard |
| [sources.lock](../../../../sources.lock), [profile](../../../../profiles/g615-v11-csf.json) | Current input pin/series; the profile still describes MC6. Neither identifies the ICD from a historical log |
| [mesa27-large-draw-initializer-fix.json](../../../../validation/mesa27-large-draw-initializer-fix.json) | HISTORICAL_REPORT Moto MC2/Android16/CSF1.21, Mesa base `13baeb70...`, ICD `c4532ef9...`, series `7d02a194...`; 8/8 direct/indirect per size. Does not validate AHB, presentation, or performance |
| [Moto results in the test guide](../../../../tests/README.md) | HISTORICAL_REPORT: shell release fails with `3e79dd98...` versus success with `d30b7c60...`; app failure precedes release. Do not combine gates across contexts |
| [Kernel/platform register](../../../../docs/engineering/mali-kernel-platform/EVIDENCE_REGISTER.md) | E-015..E-021 reconcile the pin and historical Moto evidence; preserve classification and limitations, do not reclassify as measurements from this generation |
| [PERF-PROGRESS.md](../../../../docs/PERF-PROGRESS.md) | HISTORICAL_REPORT MC6/JM, Mesa 26.3 and development builds; notes up to 2x noise between runs. Source for exercises/methodology, not a Moto baseline |
| [Perf review 2026-10-26](../../../../worklogs/g615-dxvk/perf-review-2026-10-26/README.md) | Hypotheses and estimates, FO4 under swap pressure and a present-limited cube; not measurements of Moto improvement |

## Recorded gaps

A reproducible Moto performance baseline, qualified firmware/thermal/DVFS/
counters, displayed-frame capture, compute throughput, and isolated bandwidth
are not established by these sources. Do not fill gaps with Poco/third-party
data. The skill can be documentation-ready with physical gates BLOCKED or
NOT EXECUTED and explicit next steps.

## Delivery format

1. Problem, scope, and authorization.
2. Identity and handoff; facts, observations, history, hypotheses, UNKNOWN.
3. Procedure/command, expected versus actual, samples, and artifacts.
4. Comparison/dispersion and bounded verdict.
5. Gate table, first causal failure, risks, and next test.

The generation report establishes the validity of instructions and offline
analysis, not a physical result. Final approval requires the user's decision.
