---
name: panvk-build-validation
description: "Use to prepare, build, inspect and diagnose PanVK Mesa 27 with integrated Kraid on Android/Bionic and Linux/glibc. G15 scope: Moto G86 Mali-G615 MC2, PAN_ARCH 11 and Kbase CSF. Separates provenance, build, packaging and functional validation."
---

# PanVK build diagnosis and validation

Use this skill for PanVK at the revision pinned in [sources.lock](../../../sources.lock), currently Mesa `27.0.0-devel`, on Android/Bionic and Linux/glibc. Kraid is integrated, but selected by default only on Android; glibc remains opt-in.

The documentary target is Moto G86 / Mali-G615 MC2. The G15 scope label does not replace `PAN_ARCH=11`. The only profile accepted by the scripts, [g615-v11-csf](../../../profiles/g615-v11-csf.json), still identifies the Poco X6 Pro MC6: do not copy its core mask, kernel, permissions or results to the Moto. Confirm current identity before hardware execution; unknown prerequisites remain `BLOCKED` without preventing documentary preparation.

## Routing

- [mesa3d-mali-expert](../mesa3d-mali-expert/SKILL.md): general guidance and routing.
- [kraid-compiler](../kraid-compiler/SKILL.md): NIR translation, IR, legalization, scheduling, allocation and codegen.
- [panfrost-panvk](../panfrost-panvk/SKILL.md): PanVK/Panfrost implementation and architecture.
- [mali-kernel-platform](../mali-kernel-platform/SKILL.md): Kbase, UAPI/ABI, CSF, memory and platform.
- This skill: preparation, building, packaging, inspection, test selection and evidence classification.

## Method

1. **Bound the failure.** Identify Bionic ICD, glibc ICD or application, host, stage and acceptance criterion. Consult local scripts and logs before selecting the [workflow](./references/workflow.md) procedure. Do not presume versions, flags, GPU, UAPI or success.
2. **Preserve context.** Check local changes, profile, Mesa pin, `patchSeriesId` and applied variant. Prepare a disposable copy with the intended inputs; exporting `HEAD` omits local changes. Do not edit original sources in `work/` or run scripts there that clean or reset the tree.
3. **Isolate one cause at a time.** Cite the first causal error, file or command and evidence. Change one variable and repeat only the affected gate, using a fresh `BDIR` when cross configuration changes. If testing does not narrow the failure domain, stop toggling flags and reduce the case.
4. **Use project scripts.** Explicitly select profile, NDK/toolchain and target dependencies. Do not install ad hoc packages or edit extracted Mesa. Prepare patches in the correct family; application requires authorization, a disposable tree and checks without offsets/fuzz. `--with-kbase-sync` remains opt-in, G615 only.
5. **Validate the exact result.** Inspect ELF, dependencies, symbols and identity before packaging. Select only affected tests and record evidence per gate. Do not run builds or hardware tests just to update documentation; reuse records with their original identity and limits. Hardware tests require authorization.

## Gates

Use `PASS`, `FAIL`, `BLOCKED` and `NOT EXECUTED` separately. Passing one gate does not pass the next; compilation, symbols, enumeration and ZIP integrity do not prove runtime behavior.

| Gate | Criterion |
|---|---|
| Provenance | Consistent pin, profile and input hash; application proven separately by the variant manifest and drift-free log. |
| Toolchain | Compilers, sysroot, host tools and target dependencies identified and separated. |
| Build | Compilation/link complete and expected artifacts produced at the recorded destination. |
| ELF | ELF64 AArch64, ABI, dependencies, exports and relevant notes verified; the script alone does not cover all criteria. |
| Package | Correct content/metadata, ZIP integrity and bytes/SHA-256 matching the inspected ICD. |
| Runtime | Exact ICD loaded; complete functional results for the declared test, environment and device. |
| Stability | No crash, hang, device-lost or corruption within executed cycles/limits, without extrapolating coverage. |
| Performance | Reproducible comparison on the same workload/device/configuration; no gain claimed from a build or enumeration. |

The [operational workflow](./references/workflow.md) defines prerequisites, commands, evidence and actions per gate. Compute `0x12345678` in 10/10 remains available as a smoke test; MC6 evidence does not homologate it as a Moto baseline.

## Delivery

Report diagnosis, action, per-gate results and the next verifiable step. Record profile, Mesa revision, `patchSeriesId`, variant/manifest, host, toolchain, API, Build ID and SHA-256, plus device/environment for runtime. Separate current facts, historical reports, hypotheses and unknowns; state what was not executed. Mesa driver changes require patches and approval before application; edit other files directly and review the diff. Do not commit or publish without authorization.
