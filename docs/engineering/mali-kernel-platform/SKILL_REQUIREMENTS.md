# Requirements for the future `mali-kernel-platform` skill

This is a requirements document, not the definitive `SKILL.md`.

## Scope and responsibility boundaries

The skill must own investigation of Kbase UAPI, Panthor DRM interfaces,
CSF/JM submission protocols, kernel-facing memory and synchronization,
firmware dependencies, and Android/Linux platform interfaces. It must coordinate
with PanVK and build/testing specializations without silently expanding their
scope or claiming kernel behavior from userspace code alone.

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
5. Trace the contract end to end: userspace request -> ioctl/ABI -> kernel
   handling -> synchronization/completion/error behavior -> hardware result,
   marking unknown links.
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

Use the evidence categories from
[EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md): static confirmation,
reproduction, build validation, hardware validation, historical report,
hypothesis, or unknown. A source-level observation is not a runtime result.
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

