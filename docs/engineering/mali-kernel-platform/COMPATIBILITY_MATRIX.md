# Compatibility matrix

This matrix separates implementation intent from evidence quality. "Not
verified" is not a negative compatibility result; it means the available
materials do not establish the tuple.

## Current physical reference — Moto G86

| Platform / path | Evidence | Qualification boundary |
|---|---|---|
| Android/Bionic, G615 MC2, CSF 1.21 | E-016: targeted workloads on binary `c4532ef9...`, series `7d02a194...` | Historical manifest; not full CTS, WSI or AHB qualification, and not the current `3e20d28a...` series. |
| Android WSI with driver-owned buffers | E-017: 300/300 draw cycles reported for `a273db7e...` | Historical report; external-AHB app import is a separate failure. |
| Android external-AHB app import | E-017: layout/metadata discovery fails; `FAIL (deferred)` on the documented ROM | Do not infer success from privileged-control import or driver-owned WSI. |
| Android sync-file export / wait-signal | E-017: two bounded app modes reported PASS for `a273db7e...` | Specific historical cases, not interprocess/lifetime/stress certification. |
| Android native-buffer release | E-018: candidate shell diagnostic passes; app fails before release | App release remains untested; do not confuse private-entrypoint diagnostics with system-loader presentation. |
| Linux/glibc chroot on Moto | No current-series Moto qualification established by the cited evidence | Separate build, loader, device-access, synchronization and presentation gates. Android success and Poco MC6 results do not certify it. |

All test statements in this section are `HISTORICAL_REPORT`, not fresh device
executions. See [TECHNICAL_CONSOLIDATION.md](TECHNICAL_CONSOLIDATION.md) for
the current static investigation and unknowns.

## Historical backend and device references

The tuples below are preserved as historical evidence and boundaries; they
are not an expanded support matrix for the future Moto-focused skill.

| Backend / GPU | Execution / platform | UAPI and layout evidence | Feature/path | Evidence and status | Limitations |
|---|---|---|---|---|---|
| Custom Kbase / Mali-G615 MC6, Pan arch v11 | CSF; Poco X6 Pro / Android is the historical target | Sparse analysis records CSF UAPI 1.21. `sources.lock` currently pins Mesa `13baeb70...`, while that analysis names earlier Mesa `5a07217f...`. | Sparse binding/residency | **NOT VERIFIED as currently implemented**; historical analysis says NO-GO and the tracked patch gates Kbase sparse. See E-002/E-009 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md). | Do not enable feature bits based on the later unimplemented proposal. No current device run. |
| Panthor DRM / CSF GPU | DRM node; separate kernel backend | Sparse document describes Panthor uAPI 1.9 `VM_BIND`, async bind, and DRM syncobjs. | Sparse VM bind | **Documented as a separate path; not Kbase compatibility evidence**. See E-003 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md). | No Panthor runtime test or current upstream source audit in this consolidation. |
| Kbase / JM UAPI 11.38 | Mali-G57 v9 on TB336FU; JM, per worklog | Worklog reports Kbase JM uAPI 11.38. | Shared Kbase memory allocation basic cases | **Reported historically:** `memory.allocation.basic.*` 102/102 on an earlier 110 build. See E-012 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md). | Not a CSF ioctl-layout test. The final-build rerun was skipped; no 16 KiB validation. |
| Kbase / CSF layouts, across cited DDK ranges | CSF; multiple kernel lines are mentioned in patch/worklog metadata | Patch 110 describes 32/40/112-byte group-create variants, 16/24-byte tiler-heap init layouts, and fallback; host-page calculations include 4/16 KiB. | CSF queue-group and tiler-heap initialization / page handling | **Implementation intent confirmed statically; host/build validation reported historically.** See E-005/E-012 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md). | Worklog says no CSF path ran on hardware and no 16 KiB device was available. Do not infer device support across listed UAPIs. |
| Kbase / JM v6, v7, v9 | JM; devices and kernel versions vary | UAPI/layout per tuple: **unknown** in the reviewed materials. | Sparse shadow-tile proposal / other JM paths | **NOT VERIFIED**; worklog proposal includes this scope but labels itself research/design only. See E-004 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md). | No hardware result may be inferred from the proposed architecture grouping. |
| Kbase / CSF v10, v11, v12, v13, v14 | CSF; multiple GPU architectures | Proposal groups v10-v13 with CSF UAPI >=1.9 and treats v14 separately; actual exact device UAPI varies/unknown here. | Sparse shadow-tile proposal | **NOT VERIFIED**. See E-004 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md). | Design only; sparse feature exposure remains gated until implementation and testing. |
| Kbase / G615 MC6 | CSF; historical beta.10 PanPlay and glibc chroot | Worklog 091 records a Kbase dma-heap import path, but no exact kernel/UAPI revision in the excerpt. | `VK_EXT_map_memory_placed`, memory/synchronization CTS | **Reported historically:** device results and 4520/4533 CTS outcomes. See E-006/E-013 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md). | Not rerun. Kernel/firmware/build IDs and raw-log integrity need confirmation before reuse; coherent memory does not establish external-fence completion. |
| Kbase / CSF G615 | CSF; historical `g615-v11-csf` build | Worklog 192 names Mesa `98c8b2f` plus patch chain; this differs from current pin. | Asynchronous heap termination / queue submission / sync_file paths | **Build reported; hardware NOT RUN.** See E-007/E-013 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md). | Imported waits and sync_fd export are distinct documented paths; do not claim runtime safety, performance gain, or universal concurrency behavior. |

## Explicitly unknown

- Exact Kbase UAPI, DDK, kernel commit, firmware, and Android build for each
  supported device/profile.
- Whether historical patch series and worklog source revisions match currently
  shipped binaries.
- Whether Panthor or Kbase results transfer to another backend or GPU
  generation.
- End-to-end WSI and AHardwareBuffer compatibility by device and kernel.
- Runtime behavior of the proposed sparse implementation.

