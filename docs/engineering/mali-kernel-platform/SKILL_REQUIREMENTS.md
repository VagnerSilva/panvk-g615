# Requirements for the future `mali-kernel-platform` skill

This is a requirements document, not the definitive `SKILL.md`.

## Operational development extension — second plan

The [operational revision](OPERATIONAL_DEVELOPMENT.md) adds the development
map, decision rules and correction/feature/refactor/optimization workflow.
It reuses the consolidation rather than commissioning new domain analyses.
Acceptance requires five representative development exercises, not merely
the earlier diagnostic/navigation walkthroughs. The user authorized direct
installation under Plan 2 on 2026-11-23; Mesa patch application and physical
validation remain unauthorized.

## Generated proposal — Stage 3, 2026-11-23

The proposed [skill entry point](../../../.agents/skills/mali-kernel-platform/SKILL.md)
now links ten technical references and five bounded workflows. Central Mesa/Mali
and PanVK routing links point to it while retaining availability/scope checks.
Generation does not imply installation, contract approval or hardware
qualification. On 2026-11-23 the user explicitly approved the operational
contract and its recorded limits, without authorizing application, installation
or hardware tests. Stage 4's independent initial disposition is PARTIAL;
findings, executor corrections and final approval boundaries are recorded in
[audit/SKILL_AUDIT_CLOSURE.md](audit/SKILL_AUDIT_CLOSURE.md).
Stage 2 implementation findings and deferred failures remain explicit.

## Scope and responsibility boundaries

The proposed skill is limited to the plan's G15 scope, with Moto G86 /
Mali-G615 MC2 as the physical reference, Android/Bionic and Linux/glibc in a
chroot on that Android handset. G615 uses `PAN_ARCH=11`; do not interpret
the G15 label as `PAN_ARCH=15`. Other GPUs, Linux native and Panthor runtime
support are outside scope.

The skill must own investigation of Kbase UAPI/ABI, applicable CSF submission,
kernel-facing memory and synchronization, observable firmware dependencies and
platform interfaces. Panthor and JM are boundaries or historical references,
not interchangeable backends or additional validation targets. It must
coordinate with PanVK and build/testing specializations without duplicating
their procedures or claiming kernel behavior from userspace code alone.

Treat Kraid migration as the plan's completed architectural decision, while
separating clean Mesa source, downstream patches and tested binaries.
Poco G615 MC6 evidence never establishes Moto G615 MC2 compatibility.
Use [TECHNICAL_CONSOLIDATION.md](TECHNICAL_CONSOLIDATION.md) for the current
baseline, evidence and deferred failures. The user explicitly approved these
limited operational requirements on 2026-11-23. That acceptance does not
authorize applying this patch or claim independent final homologation.

It must explicitly distinguish:

- Mesa/PanVK userspace, kernel driver/UAPI, firmware, OS/platform, and
  application behavior.
- Kbase from Panthor.
- CSF from JM.
- GPU architecture generation from execution backend.
- Source implementation, advertised feature, successful build, software test,
  device execution, and stability/performance evidence.

## Required investigation workflow

1. Read repository `AGENTS.md`; inspect branch, revision, status, protected
   source boundaries, and all existing diffs before changing anything.
2. Record `sources.lock`, exact patch series/profile, source-tree HEAD and
   modifications, host/target environment, GPU, kernel/UAPI, firmware, and
   platform.
3. Verify that specialized skills exist before routing work. Do not invent
   unavailable procedures.
4. Locate exact source/header definitions and call sites in the matching
   revision. Treat external repositories and historical worklogs as leads,
   not proof of the current implementation.
5. Trace the observable contract: userspace request -> ioctl/ABI ->
   synchronization/completion/error behavior -> recorded hardware result.
   Inspect matching kernel handling only when an authoritative source exists;
   otherwise mark that link unknown, without blocking skill generation.
6. For every claim, provide a precise source locator, revision, tuple, evidence
   class, and limitations.
7. Keep proposed designs and hypotheses separate from implemented behavior.
   Never enable or claim a capability from feasibility analysis alone.
8. Produce bounded, non-destructive validation procedures. Require explicit
   authorization and a supported target before hardware tests.
9. Report build, static, software-test, hardware, stability, and performance
   gates independently.

## UAPI and ABI requirements

- Record ioctl number, direction, structure size, alignment, field offsets,
  reserved fields, version/compat layouts, and 32/64-bit behavior where
  applicable.
- Tie each layout to an exact kernel/DDK source revision or documented UAPI
  version; do not infer ABI compatibility from a matching ioctl name.
- Cover page-size assumptions, pointer widths, address-space rules, and
  version fallback/error handling.
- Test ABI layout with static assertions or equivalent host checks; label
  hardware/driver compatibility separately.
- Never reuse a Kbase structure for Panthor or assume JM/CSF layouts are
  interchangeable.

## Memory and synchronization requirements

- Trace allocation, VA ownership, backing/import, mmap, binding, CPU/GPU
  visibility, cache maintenance, release, and error cleanup.
- For dma-buf, dma-heap, ION, and AHardwareBuffer, record handle type,
  exporter/importer, metadata/modifier, ownership transfer, and synchronization
  contract.
- Distinguish execution dependency, memory dependency, cache maintenance,
  visibility, completion, and presentation.
- Analyze binary/timeline/fence/sync_file paths separately, including queue
  ordering, import/export, wait timeout, failure, teardown, and kernel error.
- Do not infer sparse mapping, blackhole PTEs, or async VM binding from
  grow-on-fault, alias, or ordinary allocation behavior.

## Compatibility and evidence requirements

Each compatibility statement must be scoped by GPU model/PAN_ARCH, backend,
CSF/JM, exact kernel/UAPI and firmware if known, platform, source revision,
configuration, and test case. Unknown values stay unknown.

Use `STATIC_CONFIRMED`, `REPRODUCED`, `BUILD_VALIDATED`,
`AUTOMATED_TEST_VALIDATED`, `DEVICE_VALIDATED`, `HISTORICAL_REPORT`, `INFERRED`,
`HYPOTHESIS` and `UNKNOWN`, as specified by the current plan. Preserve the older
grades in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md) as historical labels.
A source-level observation is not a runtime result. Tests described by earlier
reports are historical until their original evidence is checked; they are not
new executions against the current patch series.
Store support status separately from evidence quality; never generalize a
single device result to a generation.

## Repository integrity and patch preparation

- Treat `work/` source trees as read-only.
- Do not apply patches, overwrite existing user documents, discard untracked
  content, change pinned inputs, or commit without explicit authorization.
- Prepare source changes only as isolated reviewable patch files in the proper
  family; verify exact base revision and patch metadata.
- Before applying any patch, require explicit authorization and the documented
  patch check in a disposable copy.
- Preserve historical artifacts and record provenance instead of replacing
  old results with summaries.

## Security and operational safety

- Treat kernel ioctl inputs, user pointers, DMA mappings, address arithmetic,
  lifetime races, and synchronization as security-sensitive attack surfaces.
- Review bounds, integer widths, ownership, teardown races, and error paths
  without making exploitability claims absent evidence.
- Do not run broad or destructive commands on protected trees or devices.
- Hardware tests must have bounded workloads/timeouts and an identified,
  authorized device; stop on hangs, kernel faults, or data-loss risk.
- Do not publish external source content or secrets; cite provenance and
  licenses when external references are necessary.

## Patch readiness gates

A kernel/platform patch is ready for review only when:

- The exact affected interface and kernel/DDK versions are identified.
- The root cause is distinguished from observations and hypotheses.
- The patch family/backend/profile is correct and scope is minimal.
- ABI layout, lifetime, memory visibility, synchronization, and error cleanup
  are addressed.
- Regression tests and exact validation limits are recorded.
- No runtime, performance, or cross-generation claim exceeds the executed
  evidence.

