---
name: mesa3d-mali-expert
description: >-
  Entry point for Mesa/Kraid, Panfrost/PanVK and Mali tasks when the subsystem
  is unknown or several domains interact. Classify the objective, route to
  installed compiler, Vulkan, kernel/platform, build or GPU-testing skills,
  and coordinate global compiler integration without assuming project paths.
---

# Mesa 3D and Mali Engineering

Classify tasks and coordinate the existing specializations. The user need
not know a directory, symbol, backend, or skill name before asking for help.
Do not replace the specialists or reproduce their technical procedures.

## 1. Authority and boundaries

Follow [AGENTS.md](../../../AGENTS.md) and applicable user instructions for
authority, approvals, protected sources and change workflows. A specialist
owns its technical procedure; this skill owns routing, not technical precedence.
Preserve approved architectural decisions. If procedures conflict, identify
the concrete conflict and obtain a decision before the affected action;
continue only independent, non-conflicting work.

Loading a skill grants no permission for Mesa patch application, hardware
access/tests, installation, mounts, cleanup, commits or publication. Preserve
originals and user changes; use the authorized Mesa patch workflow in a
disposable copy, never edit protected sources.

## 2. Architectural and operational scope

Preserve Kraid as a global Mesa/Panfrost compiler backend and shared upstream
compiler/model infrastructure. This is not a promise of wider driver support
or permission to replace legacy paths.

The operational target is Moto G86 / Mali-G615 MC2 /
MT6878 / PAN_ARCH 11 / Kbase CSF, Android/Bionic and glibc in a chroot on the
same Android handset. Android 16 is a documentary target pending confirmation.
Use [sources.lock](../../../sources.lock) and inspect the actual configuration;
do not assume identical compiler selection between ABIs.

The [g615-v11-csf profile](../../../profiles/g615-v11-csf.json) contains Poco
MC6 identity, not Moto MC2 evidence. Never copy its mask, UAPI, permissions or
results to the Moto. JM, Panthor, Linux-native and other GPUs are historical
or interface boundaries here, not newly qualified targets. Do not expand
the operational scope without approval.

## 3. Classify before locating code

Check operational scope before assigning an execution owner. A request for
JM, Panthor, Linux-native or another GPU stays with this central skill for
a scope decision, even if the objective is a benchmark or implementation.
Do not hand off execution to an out-of-scope specialist before approval.
Missing device identity alone does not prevent documentary classification.

1. Identify the requested outcome: implementation/correction, build/package,
   execution/measurement, or architectural coordination.
2. Identify the first evidenced failure stage, not a presumed root cause.
   A word such as "compilation", "memory" or "sync" alone does not select a skill.
3. Select one primary owner below and only evidenced dependent domains.
   If the stage is unknown, inspect the supplied error/log; if still
   ambiguous, request the smallest discriminating information through the
   available clarification tool. Do not require the user to supply project paths.
4. Verify the linked entry exists, then load the selected skill through the
   available skill mechanism and inspect its current scope before execution.
   The specialist locates the relevant implementation and procedures.
5. Report: objective, primary skill and reason, conditional dependencies and
   order, scope/authorization limits, and next discriminating step.
   A provisional owner is not a confirmed cause.

| Requested outcome / evidenced domain | Primary owner | Boundary |
|---|---|---|
| NIR-to-Kraid translation, IR, passes, scheduling, liveness, allocation, spilling, ISA, codegen, compiler-unit tests | [kraid-compiler](../kraid-compiler/SKILL.md) | Not Meson/Rust toolchain failures or device benchmark execution |
| Vulkan contracts, features, objects, pipelines, descriptors, resources, barriers, submission construction, WSI; relevant Panfrost shared interfaces | [panfrost-panvk](../panfrost-panvk/SKILL.md) | Owns compiler selection/input/output contracts, not Kraid internals or kernel ABI |
| Kbase ioctl/UAPI/ABI, CSF protocol, GPU VA/allocation/import, DMA-BUF, sync_file/KCPU, platform access/context | [mali-kernel-platform](../mali-kernel-platform/SKILL.md) | Not Vulkan memory/dependency semantics or build configuration |
| Meson/Ninja/NDK/Rust toolchain, cross-build, link, ELF, loader dependencies, ICD package/provenance | [panvk-build-validation](../panvk-build-validation/SKILL.md) | Build/package proof is not behavioral validation |
| Functional/CTS execution, regression reproduction, stability, benchmark, profiling, comparative optimization evaluation | [gpu-testing-profiling](../gpu-testing-profiling/SKILL.md) | Does not implement a suspected driver/compiler/kernel fix or validate packages |
| Global Kraid integration, Mesa migration, shared architecture, legacy compatibility, upstream divergence | This central skill | Coordinate existing owners of affected interfaces; no dedicated migration skill is installed |

For concrete ambiguous cases and sequencing, consult the
[responsibility matrix](references/responsibility-matrix.md), not every
specialist by default. If an entry is unavailable or out of scope, state the
gap; retain coordination using verified repository guidance or request a
scope decision. Never invent or invoke a missing specialization.

## 4. Coordinate only necessary dependencies

- Keep one coordinated flow. Load specialists as their stage becomes necessary;
  their links back here are handoffs, not instructions to restart classification.
- Separate diagnosis from delivery gates. A confirmed Kraid translation failure
  starts in compiler; a toolchain failure starts in build. After a Mesa fix,
  build validates the candidate; GPU testing follows only for required behavior.
- A CSF ioctl-layout defect starts in platform. Involve PanVK only if its
  caller contract changes, then build and authorized focused GPU validation.
- An unexplained slow Vulkan workload starts in GPU profiling. Route a fix to
  compiler, PanVK or platform only after measurements identify the domain.
  Do not infer a cause or improvement from spill counts or FPS alone.
- Reuse evidence with its original identity; do not repeat completed analysis,
  rebuild to write documentation, or activate every domain as a checklist.
- Keep revisions/configurations consistent and avoid concurrent edits to the
  same files. Parallel agents are optional, only for independent bounded work.

A handoff contains: objective/reproducer; exact revision, profile, series and
ABI/compiler selection; device/process context and binary identity when
applicable; discovered paths/symbols/interfaces; collected evidence and tested
hypotheses; proposed change/compatibility risks; actual gates, approvals and
remaining unknowns. Paths are discovered during work, not required at entry.

## 5. Evidence, validation and completion

Distinguish **Confirmed**, **Observed**, **Hypothesis** and **Unknown**.
Prefer current revision-bound implementation and matching interfaces/specs
over historical reports. Verify symbols, paths, flags and commands before use.
Keep Mesa, compiler, kernel, firmware, platform and workload separate; do not
transfer Bifrost assumptions to Kraid or JM semantics to CSF.

Use one falsifiable hypothesis and one changed variable per experiment.
Preserve historical evidence in the designated project knowledge system
(including MEM-MALI when applicable), without silently rewriting it or
treating it as more authoritative than current reproducible evidence.

Report independent gates as `PASS`, `FAIL`, `BLOCKED` or `NOT EXECUTED`:
build, static/package, functional, stability and performance. A build or
enumeration does not prove execution; one run does not prove stability;
performance requires a controlled comparison.

Respond concisely in the user's language. Completion requires the requested
scope, reviewed changes, actual verification results and limitations, and
the required approvals. Routing exercises validate documentary decisions,
not driver behavior or hardware support. Integration records:
[inventory](references/inventory.md) and [routing audit](references/routing-audit.md).
