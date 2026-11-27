# Architecture and provenance

## Scope

Kernel-facing userspace and platform boundaries for Moto G86/G615 MC2.
Read the [entry point](../SKILL.md), not this reference as a support matrix.

## Sources and confirmed boundaries

- [Project architecture](../../../../docs/ARCHITECTURE.md:3): Bionic app/loader/
  AHB/WSI → PanVK → Kbase → Android kernel; glibc uses its own loader/ICD/JSON.
- [G615 scope](../../../../docs/superpowers/specs/2026-11-21-g615-only.md:3):
  glibc means userspace chroot on the same Android handset, not Linux-native.
- [Baseline reconciliation](../../../../docs/engineering/mali-kernel-platform/TECHNICAL_BASELINE.md):
  clean Mesa and downstream Kbase are distinct; Kraid is conditionally linked.
- [Selection](../../../../scripts/apply-patches.sh:27): default families
  `common android kbase-common app-loader wsi csf csf-v11`; an overlay is copied
  after its family's patches. An isolated overlay is not a final applied tree.
- [Input hash](../../../../scripts/compute-patch-series-id.py:54) includes
  experimental inputs; [artifact provenance](../../../../scripts/build_provenance.py:26)
  must identify the selected variant and applied series separately.

## Rules and limits

Keep four identities: clean Mesa pin, downstream inputs/selection, actual
applied snapshot and tested binary. Matching pin or input hash alone does not
connect all four. Do not silently recompute a lock to hide a mismatch.

MC2 core count does not replace product/PAN_ARCH/frontend/UAPI identification.
Do not infer PAN_ARCH 15 from G15 or copy MC6 masks into Moto.
Panthor VM_BIND/syncobj is a different interface; JM is not a CSF build flag.

The consolidation is dated evidence, not proof that future revisions retain
the same contracts. F0–F5 numbering remains unmapped without original artifacts.
Use [discovery](../workflows/platform-discovery.md) and the
[evidence contract](validation.md) to report mismatches and unknowns.
