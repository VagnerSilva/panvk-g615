# Investigation backlog: F6-F12

## Current targeted backlog — 2026-11-23

The packages below are retained as historical proposals, not the current
execution order or canonical phase definitions. For the current G15 / Moto G86
scope, do not investigate additional GPUs, Panthor or JM beyond interface
boundaries. Linux/glibc means a chroot on the Android handset.

Follow [TECHNICAL_CONSOLIDATION.md](TECHNICAL_CONSOLIDATION.md) for targeted
gaps and reusable evidence. Missing F0-F5 definitions, internal kernel sources,
firmware details and untested hardware cases do not prevent generating a skill
with explicit limitations. App-UID external-AHB import remains a deferred
failure on the documented ROM; do not reopen it as a prerequisite.

The next deliverable is the proposed operational contract and skill, not a new
multigeneration ABI or hardware campaign. Hardware tests, patch application,
profile changes and commits still require explicit authorization.

## Historical proposed packages

The source plan says F6-F12 remain, but does not define their canonical
titles or scopes. The entries below are **proposed work packages**, not an
authoritative reconstruction of the original phase numbering. Confirm the
phase mapping with the plan owner before treating these labels as fixed.

## F6 — Recover and map F0-F5 source artifacts

- **Objective:** Obtain the original F0-F5 definitions, reports, handoffs, and
  phase-to-source index; map each claim to evidence IDs.
- **Why:** The current inventory cannot verify completeness of F0-F5; this
  documents a bounded inventory gap and does not prove that no phase artifacts
  exist outside the reviewed workspace materials.
- **Dependencies:** Access to the original reports/session outputs and their
  source revisions.
- **Evidence needed:** Phase definitions, immutable source references,
  revisions, test logs, device/kernel/firmware identifiers.
- **Procedure:** Reconcile each phase claim with the existing E-IDs; add
  missing items without replacing the evidence sources.
- **Exit:** Every F0-F5 phase has a documented scope, artifact list, and
  evidence status; unresolved gaps remain explicit.

## F7 — Normalize Kbase and Panthor UAPI compatibility

- **Objective:** Build a versioned comparison of Kbase ioctl/UAPI and Panthor
  DRM VM_BIND/synchronization interfaces.
- **Why:** The current sparse report warns against transferring Panthor
  behavior to Kbase, but full version-by-version evidence is absent.
- **Dependencies:** F6 provenance mapping; clean source snapshots and matching
  kernel headers.
- **Evidence needed:** Exact header/source commits, ioctl numbers and struct
  sizes/offsets, feature gates, sync contracts, device version reports.
- **Procedure:** Extract structures from matching kernel sources; compare
  userspace call sites; run static ABI/layout assertions in disposable builds.
- **Exit:** Matrix entries identify kernel revision and source for each ABI;
  no unsupported cross-backend assumptions remain.

## F8 — Verify CSF/JM layouts and generation tuples

- **Objective:** Validate CSF and JM interfaces separately across the
  architecture/profile combinations in the project.
- **Why:** Patch 110 documents layout selection but does not establish a
  complete device matrix.
- **Dependencies:** F7; authorized hardware or reproducible kernel test
  environments.
- **Evidence needed:** GPU product/architecture, DDK/UAPI version, ioctl
  layout, page size, firmware, initialization logs, host tests.
- **Procedure:** Exercise layout selectors and device initialization with
  bounded test cases; keep JM and CSF reports independent.
- **Exit:** Each claimed tuple has reproducible source and test evidence or is
  explicitly marked not verified.

## F9 — Audit DMA-BUF, dma-heap, and coherency paths

- **Objective:** Trace allocation, import/export, mmap, CPU/GPU coherency, and
  fallback behavior for dma-heap, ION, AHardwareBuffer/gralloc, and placed maps.
- **Why:** The existing placed-map report identifies dma-heap as a limitation.
- **Dependencies:** F6 provenance; exact PanVK/Kbase code and Android
  allocator/kernel sources.
- **Evidence needed:** Handle ownership, ioctl flags/results, cache sync path,
  allocator availability, build IDs, device logs, targeted memory tests.
- **Procedure:** Follow allocation through import, bind/map, use, synchronization
  and destruction; test both supported heap and missing-heap cases.
- **Exit:** Per-platform behavior and errors are known; no coherency claim is
  based solely on a feature flag or worklog summary.

## F10 — Verify sync_file and queue completion semantics

- **Objective:** Trace imported/exported sync_file, queue waits/signals,
  cross-queue dependencies, CPU waits, and error/teardown behavior on Kbase.
- **Why:** Worklog 192 identifies blocking waits and unvalidated asynchronous
  heap termination; worklog 091 references prior sync_file gaps.
- **Dependencies:** F7/F8; matching kernel/UAPI and PanVK source.
- **Evidence needed:** Call chains, ioctl behavior, synchronization tests,
  kernel logs, bounded stress and teardown results.
- **Procedure:** Test same-queue and cross-queue waits, imported/exported
  fences, timeout/error paths, and repeated device teardown. Do not mix CSF
  and JM semantics.
- **Exit:** Each dependency path has a tested completion/error result for an
  exact device/kernel tuple.

## F11 — Validate Android WSI and external buffers

- **Objective:** Complete the Android-specific AHardwareBuffer/gralloc,
  swapchain, acquire/present, and synchronization trace.
- **Why:** The reviewed evidence set does not establish a complete per-device
  WSI matrix; relevant WSI source/patch references are present, but were not
  exhaustively traced or validated.
- **Dependencies:** F9/F10; supported authorized device and current target
  build.
- **Evidence needed:** Android API/build, allocator implementation, formats and
  modifiers, import/export metadata, acquire/present logs and test outcomes.
- **Procedure:** Exercise bounded swapchain create/acquire/present/destroy and
  imported-buffer cases on each claimed platform; keep offscreen tests
  separate.
- **Exit:** WSI status is recorded per exact platform/kernel/profile, with
  hardware evidence or explicit gaps.

## F12 — Finalize operational skill requirements and validation

- **Objective:** Convert the audited findings into the future
  `mali-kernel-platform/SKILL.md` workflow.
- **Why:** The current skill directory contains a plan, not a reviewed
  definitive skill procedure.
- **Dependencies:** F6-F11 and independent audit closure.
- **Evidence needed:** Approved source boundaries, routing rules, evidence
  schema, validated UAPI/device examples, safety constraints, test procedures.
- **Procedure:** Draft requirements, review them against repository
  `AGENTS.md` and the central Mesa skill, then obtain independent review before
  creating the final skill.
- **Exit:** Requirements are approved, contradictions are resolved or
  explicitly bounded, and the final skill is created only in a separately
  authorized task.
