# Technical baseline: Mali kernel platform

## Current baseline reconciliation — 2026-11-23

The original inventory below is preserved as a historical snapshot, not a
description of the current checkout. The current project HEAD is
`b64d2fb10e191a8f5666bb509a27b4422df6030f` on `feat-migration`.
`work/mesa` is clean at the pinned commit
`13baeb70c066a9f82d2bcfb29f06e4865212affa`, version `27.0.0-devel`,
branch `repo-clean`. Porcelain status including all untracked files and both
diffs were empty. No ignored Kbase files were found in `src/panfrost/lib/kmod`.

The current `sources.lock` patch-series ID is
`sha256:3e20d28a3753e671f6cbfe164372e71b55ecf407dec039f56c05232c53bf2060`;
the profile-specific computation returned the same value. This establishes
input identity, not patch application or runtime qualification.

Kraid is present in the clean Mesa compiler tree and linked conditionally on
`with_panfrost_rust`. The clean kmod source list contains Panfrost and Panthor,
not the downstream Kbase implementation. Use the tracked patches to investigate
Kbase; do not treat the historical modified snapshot as clean upstream.

The physical reference for this skill is Moto G86 / Mali-G615 MC2, Android
and Linux/glibc in a chroot on the Android handset. Poco MC6, JM and Panthor
remain historical evidence or interface boundaries, not additional support
targets. Keep the plan's G15 scope label distinct from G615 `PAN_ARCH=11`.

See [TECHNICAL_CONSOLIDATION.md](TECHNICAL_CONSOLIDATION.md) for the targeted
investigation, platform-specific evidence and remaining limitations. Existing
F0-F5 definitions remain unavailable; domain coverage does not reconstruct
their canonical numbering.

## Historical snapshot — consolidation audited on 2026-11-21

## Purpose and evidence policy

This document consolidates the kernel/platform evidence currently present in
the repository for the planned `mali-kernel-platform` skill. It is not a
replacement for the underlying worklogs, a kernel ABI specification, or an
approval of the proposed skill.

Evidence labels used here:

- **Confirmed statically**: verified in a source or document named below.
- **Reported historically**: stated by a worklog or patch metadata; not
  reproduced in this task.
- **Hypothesis/proposal**: an approach or explanation not established by
  implementation and validation.
- **Unknown**: the available materials do not establish the claim.

The label describes the evidence, not the completeness of feature support.
Build, CTS, hardware, and kernel/firmware results remain separate.

## Provenance and current workspace

| Item | Recorded value |
|---|---|
| Repository branch / HEAD | `feat-migration` / `ef857062b90ee2448a5b812596ba8affb94ddcf6` |
| Pinned Mesa input | `13baeb70c066a9f82d2bcfb29f06e4865212affa`, Mesa `27.0.0-devel`, pinned 2026-11-04 |
| `sources.lock` patch series ID | `sha256:2657b6a07bb15978a66cb43cc50fff6c19e738e39f91782379637013eaad0e3a` |
| Checked-out `work/mesa` HEAD | Matches the pinned Mesa commit |
| `work/mesa` status | Not clean: many modified files and untracked files, including Kbase UAPI/backend sources |
| Profile | `g615-v11-csf` is the documented development baseline; an active build profile for this task was not established |
| Current validation | No build, test suite, or device test was run for this documentation task |

`work/mesa/` was treated as read-only. Source observations from that tree are
scoped to its modified working state, not clean upstream Mesa. The patch series
ID is recorded from `sources.lock`; it was not recomputed.

## Architecture and boundaries

### Kbase and Panthor are separate kernel interfaces

The project has a custom userspace Kbase backend for Android `/dev/mali0`.
Kbase uses its own ioctl/UAPI and memory model. Panthor is a DRM kernel driver
whose VM operations use Panthor DRM `VM_BIND` and DRM synchronization objects.
The repository's sparse feasibility note explicitly warns against applying
Panthor's sparse path to the Kbase backend. **Confirmed statically in the
repository's documentation and patch series; not an independent kernel
implementation audit.** See [E-002](EVIDENCE_REGISTER.md) and
[E-003](EVIDENCE_REGISTER.md).

### CSF and JM are not interchangeable

CSF and JM have different queue/submission interfaces and UAPI structures.
Patch 110 records version-dependent CSF ioctl layouts and page-size handling;
the Kbase backend also contains a separate legacy-JM version check in the
modified source snapshot. No finding here establishes that a CSF structure,
ioctl contract, synchronization path, or result transfers to JM (or vice
versa). See E-005/E-009 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md).

### Memory and synchronization

The existing sparse feasibility analysis states that Kbase UAPI 1.21 lacks
the Panthor-style arbitrary-VA bind/unbind and async VM-bind contract required
by the then-audited PanVK sparse path. A later worklog proposes a different
"shadow-tile sparse" design for some non-aliased cases; it is explicitly
research/design only and does not overturn the documented runtime gate until
implemented and validated. `sparseResidencyAliased` remains separately
unproven/unsupported in those materials. See [E-002](EVIDENCE_REGISTER.md)
and [E-004](EVIDENCE_REGISTER.md).

For placed host mappings, worklog 091 reports a dma-heap-backed shared BO
approach and historical device/CTS results. It also records failure when
dma-heap is unavailable. These are historical results from the beta.10 tree,
not a current-tree rerun. See E-006/E-013 in
[EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md).

Worklog 192 describes a CSF Kbase submission change and explicitly says it was
not run on hardware. Its sync-wait and heap-termination measurements are
historical reports, not a current performance or correctness claim. See
E-007/E-013 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md).

## F0-F5 consolidation status

The supplied plan names F0-F5 but does not define their individual scope or
provide a phase-to-artifact index. The current repository inventory found no
F0-F5 report set or mapping. Therefore:

- **F0-F5 phase completion: UNKNOWN / NOT VERIFIABLE from available inputs.**
- The evidence register captures relevant materials that do exist, with their
  provenance and limitations.
- Evidence topics below must not be retroactively assigned to a particular
  F-phase without the missing phase definitions or original handoffs.
- The original inventory reported an empty `docs/engineering/EVIDENCE_REGISTER.md`
  as preserved. That ancestral file is absent in the 2026-11-23 inventory;
  its contents are not reconstructed. This consolidation remains in its own
  directory.

The available material covers: Kbase sparse feasibility and a later
unimplemented design proposal; CSF UAPI layout compatibility; placed
dma-heap mappings; asynchronous CSF submission; and broad Mali architecture
notes. It does not provide a complete kernel-version/device matrix, a clean
source snapshot, or current reproducible logs for every reported result.

## Compatibility conclusions

The current evidence supports only narrowly scoped statements:

1. A historical G615/CSF Kbase analysis records UAPI 1.21 and a sparse
   **NO-GO** for the analyzed implementation/revision.
2. The tracked Kbase patch family gates sparse exposure for the Kbase path.
3. Patch 110 documents CSF UAPI layout fallback and 4/16 KiB host-page
   handling; its metadata records JM UAPI 11.38 test context and a host
   assertion test plus an Android build. Those are not proof of device
   compatibility across all listed DDKs.
4. Panthor `VM_BIND` evidence is a separate backend reference, not Kbase
   compatibility evidence.
5. JM v6/v7/v9 and CSF v10-v14 statements in the sparse research note are
   proposed design scope, not a completed compatibility certification.

The detailed tuples, unknowns, and evidence grades are in
[COMPATIBILITY_MATRIX.md](COMPATIBILITY_MATRIX.md).

## Limitations and next verifiable steps

- Obtain the authoritative F0-F5 definitions, outputs, and original phase
  references before claiming full consolidation.
- Re-run static checks against a clean, authorized source snapshot at the
  pinned revision; do not alter the current `work/mesa`.
- Establish exact kernel/DDK/UAPI versions, GPU, firmware, Android build, and
  runtime for each claimed compatibility tuple.
- Verify the original raw logs/reports for historical device and CTS results.
- Test the proposed sparse design only under a separately approved bounded
  device procedure; do not enable sparse feature bits based on the design note.
- Complete the independent audit documented in
  [`audit/CONSOLIDATION_AUDIT.md`](audit/CONSOLIDATION_AUDIT.md).
