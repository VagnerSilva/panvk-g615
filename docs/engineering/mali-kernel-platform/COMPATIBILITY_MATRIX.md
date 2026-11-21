# Compatibility matrix

This matrix separates implementation intent from evidence quality. "Not
verified" is not a negative compatibility result; it means the available
materials do not establish the tuple.

| Backend / GPU | Execution / platform | UAPI and layout evidence | Feature/path | Evidence and status | Limitations |
|---|---|---|---|---|---|
| Custom Kbase / Mali-G615 MC6, Pan arch v11 | CSF; Poco X6 Pro / Android is the historical target | Sparse analysis records CSF UAPI 1.21. `sources.lock` currently pins Mesa `13baeb70...`, while that analysis names earlier Mesa `5a07217f...`. | Sparse binding/residency | **NOT VERIFIED as currently implemented**; historical analysis says NO-GO and the tracked patch gates Kbase sparse. See E-002/E-010 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md). | Do not enable feature bits based on the later unimplemented proposal. No current device run. |
| Panthor DRM / CSF GPU | DRM node; separate kernel backend | Sparse document describes Panthor uAPI 1.9 `VM_BIND`, async bind, and DRM syncobjs. | Sparse VM bind | **Documented as a separate path; not Kbase compatibility evidence**. See E-003 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md). | No Panthor runtime test or current upstream source audit in this consolidation. |
| Kbase / JM UAPI 11.38 | Mali-G57 v9 on TB336FU; JM, per worklog | Worklog reports Kbase JM uAPI 11.38. | Shared Kbase memory allocation basic cases | **Reported historically:** `memory.allocation.basic.*` 102/102 on an earlier 110 build. See E-006/E-012 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md). | Not a CSF ioctl-layout test. The final-build rerun was skipped; no 16 KiB validation. |
| Kbase / CSF layouts, across cited DDK ranges | CSF; multiple kernel lines are mentioned in patch/worklog metadata | Patch 110 describes 32/40/112-byte group-create variants, 16/24-byte tiler-heap init layouts, and fallback; host-page calculations include 4/16 KiB. | CSF queue-group and tiler-heap initialization / page handling | **Implementation intent confirmed statically; host/build validation reported historically.** See E-005/E-012 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md). | Worklog says no CSF path ran on hardware and no 16 KiB device was available. Do not infer device support across listed UAPIs. |
| Kbase / JM v6, v7, v9 | JM; devices and kernel versions vary | UAPI/layout per tuple: **unknown** in the reviewed materials. | Sparse shadow-tile proposal / other JM paths | **NOT VERIFIED**; worklog proposal includes this scope but labels itself research/design only. See E-004 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md). | No hardware result may be inferred from the proposed architecture grouping. |
| Kbase / CSF v10, v11, v12, v13, v14 | CSF; multiple GPU architectures | Proposal groups v10-v13 with CSF UAPI >=1.9 and treats v14 separately; actual exact device UAPI varies/unknown here. | Sparse shadow-tile proposal | **NOT VERIFIED**. See E-004 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md). | Design only; sparse feature exposure remains gated until implementation and testing. |
| Kbase / G615 MC6 | CSF; historical beta.10 PanPlay and glibc chroot | Worklog 091 records a Kbase dma-heap import path, but no exact kernel/UAPI revision in the excerpt. | `VK_EXT_map_memory_placed`, memory/synchronization CTS | **Reported historically:** device results and 4520/4533 CTS outcomes. See E-007/E-013 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md). | Not rerun. Kernel/firmware/build IDs and raw-log integrity need confirmation before reuse; coherent memory does not establish external-fence completion. |
| Kbase / CSF G615 | CSF; historical `g615-v11-csf` build | Worklog 192 names Mesa `98c8b2f` plus patch chain; this differs from current pin. | Asynchronous heap termination / queue submission / sync_file paths | **Build reported; hardware NOT RUN.** See E-008/E-013 in [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md). | Imported waits and sync_fd export are distinct documented paths; do not claim runtime safety, performance gain, or universal concurrency behavior. |

## Explicitly unknown

- Exact Kbase UAPI, DDK, kernel commit, firmware, and Android build for each
  supported device/profile.
- Whether historical patch series and worklog source revisions match currently
  shipped binaries.
- Whether Panthor or Kbase results transfer to another backend or GPU
  generation.
- End-to-end WSI and AHardwareBuffer compatibility by device and kernel.
- Runtime behavior of the proposed sparse implementation.

