# Integration inventory

Date: 2026-11-24. Delivery 1: inventory of existing skills and rules.
Initial state: branch `feat-migration`, HEAD
`01bc819e0bc3b4dee61b88edf46508737e1ff07f`; only the user-supplied planning
document was untracked, with no tracked diff. It was preserved during the
original integration; the user subsequently requested its removal.
Pinned Mesa: `13baeb70c066a9f82d2bcfb29f06e4865212affa`,
`27.0.0-devel`; series recorded in
[sources.lock](../../../../sources.lock):
`sha256:3e20d28a3753e671f6cbfe164372e71b55ecf407dec039f56c05232c53bf2060`.
These are documentary inputs, not the identity of an ICD executed in this delivery.

## Existing technical skills

All six entries have frontmatter with `name` and `description`. Availability,
documentary approval, authorized installation and hardware validation are
distinct states. Missing approval in an entry does not imply rejection.

| Entry | Trigger and responsibility | Limits / observed status |
|---|---|---|
| [mesa3d-mali-expert](../SKILL.md) | General Mesa/Mali entry and coordination; classification before locating files | User accepted documentary homologation on 2026-11-24, including the R15 limitation; not hardware approval |
| [kraid-compiler](../../kraid-compiler/SKILL.md) | NIR translation, IR, passes, scheduling/RA/spill, ISA, compiler-local tests | No final approval declared in the entry; evidence is revision/model-bound, not general hardware support |
| [panfrost-panvk](../../panfrost-panvk/SKILL.md) | Vulkan contracts, compiler integration, resources/sync/submission/WSI; relevant Panfrost interfaces | No final approval declared in the entry; full Gallium is out of scope; MC6/broad-scope wording must remain bounded by the active target |
| [mali-kernel-platform](../../mali-kernel-platform/SKILL.md) | Kbase/UAPI/ABI, CSF, VA/memory, DMA-BUF/sync_file/KCPU, Android/glibc context | Entry records installation authorization on 2026-11-23, not driver/hardware approval; Moto MC2/arch 11 scope |
| [panvk-build-validation](../../panvk-build-validation/SKILL.md) | Preparation, toolchain/cross-build, ELF, packaging, provenance and build diagnosis | No final approval declared in the entry; glibc is opt-in; runtime is a separate gate |
| [gpu-testing-profiling](../../gpu-testing-profiling/SKILL.md) | Functional execution, stability, benchmarks/profiling and comparisons | Offline audit recorded; final approval belongs to the user; does not validate builds/packages or create a Moto baseline |

Platform status: the
[operational review](../../../../docs/engineering/mali-kernel-platform/OPERATIONAL_DEVELOPMENT.md)
records demonstrative exercises; the
[earlier closure](../../../../docs/engineering/mali-kernel-platform/audit/SKILL_AUDIT_CLOSURE.md)
preserves the historical PARTIAL disposition and must not be promoted to
hardware homologation or final independent approval. The
[GPU audit](../../gpu-testing-profiling/references/operational-audit.md)
also separates offline exercises, documentary approval and hardware execution.
This integration does not reapprove the specialists.

## Process skills and rules

The local catalog contains five additional skills without their own Mesa
technical responsibility:

- [using-superpowers](../../using-superpowers/SKILL.md): skill discovery/use.
- [writing-plans](../../writing-plans/SKILL.md): planning.
- [executing-plans](../../executing-plans/SKILL.md): implementation execution.
- [dispatching-parallel-agents](../../dispatching-parallel-agents/SKILL.md):
  independent parallel work, not permission to delegate every task.
- [verification-before-completion](../../verification-before-completion/SKILL.md):
  evidence before completion claims.

[AGENTS.md](../../../../AGENTS.md) defines authority, integrity, scope,
approvals and gates. The [Copilot instructions](../../../../.github/copilot-instructions.md)
record commands/conventions; their universal-release/JM examples diverge
from the active scope. The [architecture](../../../../docs/ARCHITECTURE.md)
limits exposure to G615/CSF v11 and preserves upstream infrastructure.
No additional AGENTS files were found under skills or docs.

## Overlaps, gaps and treatment

| Initial finding | Treatment in this integration |
|---|---|
| Central routed global integration to `mesa-kraid-migration`, absent from the 11 local skills | Remove nonexistent route; central coordinates interfaces with existing specialists |
| "Compilation" could mean shader translation or toolchain/link | Classify the stage: compiler for NIR/IR; build for Meson/Rust/NDK/link |
| Memory, synchronization and CSF appeared in both driver and platform | Separate Vulkan contracts/command construction from ABI/protocol/VA/fences |
| Build lists runtime gates and test selection; GPU owns execution/comparison | Build hands off provenance/artifact; GPU executes behavior and measures without revalidating packages |
| PanVK mentions a conditional testing specialist and possible migration | Central provides the real GPU route; return references do not restart the flow |
| Central/PanVK described a baseline without an operational boundary; active scope freezes Moto MC2 | Preserve global Kraid architecture without expanding operational support |
| Profile contains Poco MC6; platform/GPU scope uses Moto MC2 | Record the difference; do not change the profile or copy identity/results |
| Integrated Kraid does not prove identical Android/glibc selection | Require effective selection per ABI; do not change opt-in policy |
| Historical rules/documents differ in scope and authorization | Preserve applicable rules and decisions; concrete conflicts require a decision, not invented technical precedence |

The original integration changed no specialist, global rule, profile, pin,
Mesa source or historical evidence. The user authorized central edits and
the inventory, matrix and audit, not code, hardware, commits or publication.
The subsequent English-only cleanup translates skill documentation and removes
obsolete planning inputs and references without changing technical contracts.
