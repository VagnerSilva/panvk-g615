---
name: mali-kernel-platform
description: "Use when correcting, implementing, refactoring, optimizing or validating Kbase UAPI/ABI, CSF, GPU memory/VA, DMA-BUF, sync_file/KCPU or Android/glibc platform code for G15 and Moto G86 Mali-G615 MC2. Start from documented edit sites and contracts; investigate only blocking gaps. Route compiler, Vulkan and build work to their existing skills."
---

# Mali kernel/platform — Moto G86

Status: operational development revision authorized for installation on
2026-11-23.
The earlier limited contract was approved on 2026-11-23; its diagnostic audit
and correction history remain in the
[audit closure](../../../docs/engineering/mali-kernel-platform/audit/SKILL_AUDIT_CLOSURE.md).
The [operational review record](../../../docs/engineering/mali-kernel-platform/OPERATIONAL_DEVELOPMENT.md#operational-audit-result)
closes D1/D2 for the demonstrative exercises. The user authorized direct
installation; this does not approve driver changes or runtime support.
Loading grants no application, hardware or publication permissions.

## Scope and authority

Read [AGENTS.md](../../../AGENTS.md) and respect its approval and patch rules.
Scope uses the G15 label: Moto G86 / Mali-G615 MC2, **PAN_ARCH 11**,
Android/Bionic and Linux/glibc in a chroot on the same Android handset.
G15 does not mean PAN_ARCH 15. No Linux-native, Panthor, JM or other-GPU
runtime support is established here. Keep such evidence only as a boundary
or explicitly identified history.

Use [sources.lock](../../../sources.lock) and the selected profile, not a moving
Mesa branch. The reference is clean Mesa `27.0.0-devel` at `13baeb70...`.
Kraid migration is a completed architectural decision; distinguish
clean upstream sources, downstream Kbase patches and tested binaries.
Verify current inputs before reusing the dated
[technical consolidation](../../../docs/engineering/mali-kernel-platform/TECHNICAL_CONSOLIDATION.md).

## Non-negotiable invariants

- Preserve originals and user changes. Never edit/reset/fetch into `work/`.
  Prepare patches only for Mesa driver changes, in a separate copy; check
  exact applicability without offset/fuzz. Edit other project files directly,
  including skills, documentation, scripts, tests and apps.
  Mesa patch application, profile/contract changes, commits and publication
  require explicit approval. Do not silently approve a contract.
- Hardware access/tests, transfers, app installation, mounts and cleanup need
  explicit scope approval. A diagnostic workflow is not authorization.
- Identify device, libc, process context, UAPI, page size and exact ICD before
  execution. App, shell/root and chroot results are not interchangeable.
- Never promote MC6/Poco evidence to Moto MC2, or Android PASS to glibc PASS.
  Enumeration, a build and layout assertions are not device compatibility.
- Source/kernel/firmware are separate layers. Missing matching kernel source
  remains UNKNOWN, not a reason to invent handlers or block limited drafting.
- Stop at the first causal failure. No automatic privilege escalation,
  SELinux/linker bypass, firmware/clock write, GPU reset or unbounded retry.

## Development sequence

1. Map the task directly through [implementation recipes](references/implementation.md)
   and [decisions](references/decisions.md): known files/functions, violated
   contract, concrete edit and focused acceptance. Do not rediscover known bugs.
2. Follow [development](workflows/development.md) for correction, feature,
   refactor or optimization. Use discovery to confirm required provenance;
   use diagnostic workflows only for a concrete blocking gap.
3. Preserve the [evidence and gate contract](references/validation.md):
   `STATIC_CONFIRMED`, `REPRODUCED`, `BUILD_VALIDATED`,
   `AUTOMATED_TEST_VALIDATED`, `DEVICE_VALIDATED`, `HISTORICAL_REPORT`,
   `INFERRED`, `HYPOTHESIS`, `UNKNOWN`.
   A model/exercise is not a compiled-source or device test.
4. Make the smallest change with directly dependent call sites,
   error/cleanup cases and per-ABI validation; separate functional correctness
   from exposure, stability and measured optimization. Only Mesa driver
   changes require an isolated patch; other files use direct edits.
5. Review the diff (and Mesa patch when applicable) and report actual checks,
   source/binary/context, risks and approval boundaries. Never apply a Mesa
   patch without explicit approval.

## References and workflows

| Need | Reference | Workflow |
|---|---|---|
| Correct / implement / refactor / optimize code | [Edit-site map and recipes](references/implementation.md), [decisions](references/decisions.md) | [Development](workflows/development.md) |
| Layers, provenance, downstream selection | [Architecture](references/architecture.md) | [Discovery](workflows/platform-discovery.md) |
| Version, ioctl direction/size/layout | [Kbase UAPI/ABI](references/kbase-uapi-abi.md) | [UAPI audit](workflows/uapi-audit.md) |
| Queue/group/bind/kick/events/termination | [CSF/JM boundary](references/csf-jm.md) | [CSF audit](workflows/csf-audit.md) |
| VA, allocation/import/alias/JIT | [GPU memory](references/gpu-memory.md) | [Memory/sync audit](workflows/memory-sync-audit.md) |
| Cache, DMA-BUF, fences, waiters/KCPU | [DMA-BUF/sync](references/dma-buf-sync.md) | [Memory/sync audit](workflows/memory-sync-audit.md) |
| Firmware, energy and recovery observations | [Firmware/power](references/firmware-power.md) | [Device validation](workflows/device-validation.md) |
| Access, process context and safe stopping | [Operational security](references/security.md) | [Discovery](workflows/platform-discovery.md) |
| Android app/loader/mapper boundaries | [Android](references/android.md) | [Device validation](workflows/device-validation.md) |
| glibc loader/guest/WSI boundaries | [Linux/glibc](references/linux-glibc.md) | [Device validation](workflows/device-validation.md) |
| Evidence, gates and report shape | [Validation](references/validation.md) | All workflows |

## Known limits and handoffs

The examined import still conflates SAME_VA/NEED_MMAP despite an old documented
correction. Default waiter lifetime, sync-file CLOEXEC/deadline/revents and
partial-KCPU-enqueue handling have documented defects or unresolved contracts.
Do not call them fixed from patch presence or historical PASS.
Experimental sync 002–004 remains opt-in for `g615-v11-csf`, without 001.

Moto external-AHB import in app UID is a **historical FAIL (deferred)** on the
documented ROM; do not reopen it automatically or modify external buffers to
probe layout. Driver-owned WSI is a separate historical result. Moto glibc,
16 KiB execution, full CTS, firmware/power/recovery and general stability are
not qualified by this skill.

Route compiler internals to [Kraid](../kraid-compiler/SKILL.md), Vulkan
contracts/resources/WSI to [PanVK](../panfrost-panvk/SKILL.md), build/package
work to [build validation](../panvk-build-validation/SKILL.md), and cross-domain
coordination to [Mesa/Mali](../mesa3d-mali-expert/SKILL.md).
Verify a target skill exists and inspect its scope before loading it.
For a missing testing specialist, use verified repository tests/procedures,
not invented instructions. Hand off only the dependent part with exact
revision, context, source locators, evidence, hypotheses and open gates.
