# AGENTS.md

## Project Mission

Maintain and evolve the `panvk-kbase-android` project, including its Mesa integration, Kraid compiler backend, Panfrost/PanVK drivers, Mali GPU support, Android integration, build infrastructure, packaging, and validation systems.

The central architectural objective is to integrate Kraid as a global compiler backend within the Mesa/Panfrost project, rather than treating it as an isolated Mali-G615 experiment.

The active Mesa 27 product scope is Mali-G615 with Kbase CSF v11, represented by the sole `g615-v11-csf` profile, on Android/Bionic and Linux/glibc. Historical devices and universal releases are evidence only. Preserve upstream compiler and model infrastructure; wider driver support requires a separately approved change.

Use the Mesa revision pinned in `sources.lock`. Read the [architecture guide](docs/ARCHITECTURE.md) and the relevant technical documentation before changing project behavior.

Use Meson and Ninja for Mesa builds, including Android AArch64/Bionic and Linux/glibc targets. Use Gradle and CMake for the application components where applicable.

## Project Scope

The project covers the following engineering areas:

### Mesa and Kraid

- Mesa source migration and integration.
- Kraid compiler architecture and backend integration.
- NIR translation, lowering, and legalisation.
- Kraid intermediate representations and transformations.
- Instruction scheduling and dependency management.
- Liveness analysis and register allocation.
- Register spilling and memory management.
- ISA encoding and machine code generation.
- Compiler correctness, optimization, and diagnostics.
- Integration with existing Mesa compiler infrastructure.

### Panfrost and PanVK

- Panfrost driver architecture.
- PanVK Vulkan implementation.
- Vulkan frontend and backend integration.
- Command submission and execution.
- Shader compilation and pipeline creation.
- Synchronization, barriers, and memory dependencies.
- WSI, AHardwareBuffer, and Android integration.
- Device capabilities and feature exposure.

### Mali and Platform Integration

- Mali GPU architectures and generations.
- GPU-specific behavior and hardware limitations.
- Bifrost and newer architecture differences.
- Kbase UAPI and kernel interface.
- CSF and JM command submission models.
- GPU memory management and synchronization.
- Android/Bionic and Linux/glibc integration.
- Device-specific configuration and compatibility.

### Build, Distribution, and Validation

- Meson and Ninja build infrastructure.
- Host tools and target cross-compilation.
- Android NDK and sysroot management.
- Dependencies and reproducible builds.
- ICD validation and packaging.
- ADPKG and distribution workflows.
- CTS, runtime tests, and functional validation.
- Profiling, benchmarks, and performance analysis.

## Engineering Principles

1. Correctness comes before performance.
2. Never assume that Bifrost optimizations are valid for Kraid.
3. Distinguish architecture-independent behavior from GPU-generation-specific behavior.
4. Distinguish G615-specific behavior from common Mali behavior.
5. Preserve compatibility with existing Mesa infrastructure unless an architectural change is explicitly justified.
6. Prefer deterministic implementations and reproducible validation.
7. Do not introduce speculative hardware assumptions.
8. Do not claim performance improvements without comparative measurements.
9. Do not claim functionality is validated without executing the relevant tests.
10. Separate confirmed facts, hypotheses, and unresolved questions in technical reports.

## Agent Autonomy and Approval

The agent may autonomously:

- Inspect the repository and its documentation.
- Analyze source code, patches, build scripts, and test results.
- Investigate compiler and driver behavior.
- Identify architectural problems and potential regressions.
- Design implementation strategies.
- Prepare isolated and reviewable patches for Mesa driver changes.
- Edit other project files directly within the requested scope, preserving existing changes.
- Run non-destructive validation in disposable workspaces.
- Produce technical reports and implementation plans.

Explicit user authorization is required before:

- Applying patches to project source trees.
- Replacing existing files.
- Modifying approved contracts or architectural decisions.
- Changing pinned dependencies or Mesa revisions.
- Changing build profiles or release configuration.
- Running operations that can remove or overwrite project data.
- Creating commits or publishing changes.

Investigation and Mesa patch preparation do not imply authorization to apply
Mesa patches. Changes outside Mesa use direct edits, not a mandatory patch
delivery/application step; other approval and workspace-safety rules still apply.

## Directory Map

- `patches/` and `profiles/`: patch families and JSON profiles for GPU architecture, frontend, and Kbase interface.
- `scripts/`: Mesa setup, patch application, builds, packaging, and validation.
- `meson/`: AArch64 build configurations for Android and Linux.
- `apps/`: PanPlay (`panvk-launcher`) and PanProbe (`panvk-test`), with Gradle for app builds and CMake for native code.
- `tests/`, `device/`, and `tools/`: host test suites, on-device Vulkan tests, and utilities.
- `docs/`, `compatibility/`, `validation/`, and `worklogs/`: guides, device compatibility data, and runtime evidence.
- `.agents/`: specialized agent skills and their supporting documentation.
- `.github/workflows/`: CI automation.
- `work/`, `build/`, and `dist/`: local sources and dependencies, build directories, and artifacts, respectively. Do not commit them.
- Project dependencies live in `work/`: the pinned Mesa tree (`work/mesa/`), `work/libdrm/`, the NDK-built Android dependency prefixes (`work/android-deps/`, `work/android-deps-x11/`), the Android NDK (`work/ndk/`) and the Kbase kernel sources (`work/mali_kbase/`). Look for dependencies there before fetching or installing them elsewhere, and keep new dependencies in `work/` as well.
- `logs/`: the project's standard log-collection scripts that verify and validate data on the device via adb (for example `logs/audit_panvk_targets.sh` and `logs/check_panvk_pressure.sh`). Create new device collection and verification scripts here and reuse the existing ones before writing ad hoc adb commands.

Consult the relevant skill in `.agents/skills/` before performing specialized work. Existing skills are authoritative for their documented procedures unless they conflict with this file or an approved architectural decision.

Do not duplicate detailed technical documentation in this file. Keep project-wide rules here and specialized procedures in their corresponding skills and references.

## Repository Integrity and Workspace Safety

1. Treat original files in `work/` as read-only. Never edit, overwrite, or remove them directly, including files in `work/mesa/`, `work/libdrm/`, and `work/android-deps/`.
2. Never assume that a clean Git checkout contains all required inputs. Local changes and untracked files may be part of the intended build or investigation.
3. Inspect `git status`, the current branch, the relevant revision, and existing diffs before preparing changes.
4. Represent driver changes targeting `work/mesa/` through reviewable `.patch` files. Edit other project files directly; documentation, skills, scripts, tests and apps do not require generated patches.
5. Generate Mesa patches with `git diff --binary --full-index` in a separate copy, or write a unified diff.
6. Preserve original paths, directory structure, permissions, and data.
7. Apply Mesa patches only to a disposable copy at the correct revision, never to the original source tree.
8. Run `git apply --check --whitespace=error -v change.patch` before applying a Mesa patch.
9. Reject conflicts, offsets, or fuzz. Do not suppress patch failures.
10. Apply the patch with `git apply change.patch` only after the check passes and explicit authorization has been granted.
11. Compare the result with `git diff` or `diff`. Confirm that only intended paths, file modes, and contents changed.
12. Never use destructive Git operations such as `git reset`, `git clean`, or forced checkout without explicit authorization.
13. Never overwrite existing user changes or discard uncommitted work.

## Patch Engineering

- Every Mesa driver change targeting `work/mesa/` must be represented by a reviewable patch.
- Other project changes use direct edits and diff review; do not generate documentary or other non-Mesa delivery patches.
- Keep patches small, isolated, and traceable.
- Place each patch in the family that matches its profile and architectural purpose.
- For Mesa changes, follow the required patch header in `patches/README.md`.
- Validate patch application through `scripts/apply-patches.sh`.
- Do not mix JM and CSF implementations.
- Do not assume different DDK versions share the same UAPI.
- Preserve the intended base revision and patch ordering.
- Recompute the patch series ID when the base revision, profile, or patches change:

```sh
python3 scripts/compute-patch-series-id.py --profile g615-v11-csf
```

- Never silently change an approved patch or replace an existing patch series.
- Document dependencies between patches and any profile-specific limitations.
- Do not create commits without explicit authorization.

## Kraid Compiler Engineering

When working on Kraid, investigate the complete compilation path relevant to the issue.

Consider the following stages where applicable:

1. NIR input and shader representation.
2. NIR lowering and translation.
3. Kraid IR construction.
4. Legalisation and instruction selection.
5. Optimization and data-flow transformations.
6. Instruction scheduling and dependency handling.
7. Liveness analysis.
8. Register allocation.
9. Spilling and register pressure.
10. ISA encoding and code generation.
11. Integration with Mesa compiler interfaces.
12. Runtime execution and functional validation.

Do not assume that a failure originates in the stage where it becomes visible. Trace the data and invariants across the relevant stages.

When investigating scheduling, account for:

- Data dependencies.
- Control dependencies.
- Memory ordering.
- Barriers and synchronization.
- Register hazards.
- Implicit hardware dependencies.
- Discard and side effects.
- Instruction reordering constraints.

When investigating register allocation, account for:

- Register pressure.
- Live ranges.
- Physical register constraints.
- Spill decisions.
- Spill code correctness.
- Interaction between scheduling and allocation.

Do not modify compiler algorithms based only on theoretical expectations. Identify the violated invariant and validate the proposed correction.

## Panfrost, PanVK, and Mali Engineering

- Preserve the distinction between compiler behavior, driver behavior, kernel behavior, and application behavior.
- Identify the affected GPU architecture and generation.
- Verify the relevant hardware capabilities and UAPI.
- Do not infer support from feature enumeration alone.
- Keep JM and CSF paths separate where their interfaces or behavior differ.
- Treat Kbase and userspace driver synchronization as separate validation concerns.
- Validate memory management, command submission, synchronization, and WSI independently where appropriate.
- Do not generalize a G615 result to other Mali generations without evidence.

## Build, Validation, and Test Commands

Run builds from the repository root in a disposable workspace.

Check prerequisites in the [README](README.md#building) and the [Poco X6 Pro build guide](docs/BUILD-POCO-X6-PRO.md).

Do not run `fetch-mesa.sh` on a tree that must be preserved. It resets the checkout and removes untracked files from selected Mesa paths.

The following is the established Android build sequence:

```sh
./scripts/fetch-mesa.sh
./scripts/bootstrap-host-tools.sh
./scripts/apply-patches.sh --profile g615-v11-csf
./scripts/build-android.sh --profile g615-v11-csf
./scripts/validate-binary.sh --abi android dist/android-g615-v11-csf/libvulkan_panfrost.so
```

This sequence must run only in a disposable workspace with the intended inputs.

- For incremental Android builds after setup, run `ninja -C build/android-bionic`.
- For the Linux/glibc variant, run `./scripts/build-glibc.sh --profile g615-v11-csf`.
- For G615-only releases, follow the [release guide](docs/RELEASE.md).
- The universal preparation and v9 build entry points are retired. Do not publish a G615 build as universal.
- Keep host generators and target binaries separate.
- Use NDK-built dependencies for Android.
- Use a fresh `BDIR` after changing the cross file.
- Record the toolchain, target, API level, profile, Mesa revision, and patch series used.

Run the relevant host test suites. There is no single repository-wide test command.

```sh
python3 -m unittest discover -s tests/dxvk/profile -p 'test_*.py'
python3 -m unittest discover -s tests/runtime-features -p 'test_*.py'
python3 -m unittest discover -s tests/consumer-compat -p 'test_*.py'
python3 tests/validate-package-selfcheck.py
```

- From `apps/panvk-launcher/` or `apps/panvk-test/`, run `./gradlew :app:lintDebug` and `./gradlew :app:assembleDebug` as applicable.
- The repository root has no general C or Python linter or formatter.
- Run `git diff --check` for whitespace errors.
- Follow `work/mesa/.clang-format` for Mesa code.
- For Vulkan/Kbase tests, follow the [test guide](tests/README.md) on a supported Mali device.

Run only the tests relevant to the change, but include regression tests when the change affects shared behavior.

## Validation Requirements

Separate the following validation dimensions:

### Build Correctness

Confirm that the intended target compiles and links with the expected toolchain and configuration.

### Static and Structural Validation

Validate binary architecture, ABI, symbols, package structure, hashes, and other applicable invariants.

### Functional Correctness

Execute tests that exercise the modified functionality and verify expected results.

### Runtime Stability

Evaluate crashes, hangs, synchronization failures, memory errors, and repeated execution behavior.

### Performance

Use controlled comparative benchmarks. Record workload, device, driver revision, configuration, and measurement methodology.

A successful build does not prove runtime correctness. Feature enumeration does not prove that a feature works. Passing CI does not prove correct behavior on physical hardware.

Report each relevant gate as:

- `PASS`
- `FAIL`
- `BLOCKED`
- `NOT EXECUTED`

Never report a gate as passed without evidence.

## Hardware Testing

- Confirm the target device, GPU, Android version, Kbase version, and applicable profile.
- Use timeouts and small workloads.
- Change one variable per experiment.
- Preserve logs and the identity of the tested binary.
- Do not substitute enumeration tests for execution tests.
- Separate device compatibility from driver correctness.
- Record failures at the first causal gate.
- Do not extrapolate results to unsupported devices.

## Experimental Features

Keep `--with-kbase-sync` opt-in and limited to `g615-v11-csf`.

Read the [experimental series limitations](patches/experimental-kbase-sync/README.md) before enabling it.

Do not promote experimental patches or profiles to release status without explicit validation and approval.

## Documentation and Technical Reports

For investigations and implementation work:

- State the problem and its scope.
- Identify the relevant source revision and patch series.
- Separate observed behavior from hypotheses.
- Identify the first causal failure where possible.
- Document affected files and interfaces.
- Explain the proposed change and its expected effects.
- Include test commands and actual results.
- Identify untested paths and remaining risks.
- Preserve historical evidence in the appropriate worklogs.

Use concise, scoped commit subjects when commits are explicitly authorized. Follow recent prefixes such as:

- `feat(tests):`
- `feat(patches):`
- `docs(copilot):`
- `panvk:`

## Completion Criteria

Before declaring a task complete:

1. Confirm that the requested scope was addressed.
2. Review the complete diff; for Mesa changes, also review the prepared patch.
3. Check for unintended modifications.
4. Run `git diff --check`.
5. Execute the relevant build and test gates.
6. Record all validation results.
7. Identify anything not executed or still blocked.
8. Confirm that no original source, user data, or unrelated changes were overwritten.
9. Present the changes for review; include a patch only for Mesa driver changes.

Do not apply a Mesa patch, create a commit, or publish a release without the required explicit authorization.
