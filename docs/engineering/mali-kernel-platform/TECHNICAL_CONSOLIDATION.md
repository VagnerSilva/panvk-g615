# Targeted technical consolidation — Mali kernel platform

Date: 2026-11-23. Scope: the plan's G15 label, Moto G86 / Mali-G615 MC2,
`PAN_ARCH=11`, Android/Bionic and Linux/glibc in a chroot on the same Android
handset. No Linux-native, Panthor, JM or additional-GPU runtime qualification.

This document integrates three separately produced investigations:
Kbase/UAPI/CSF; memory/DMA-BUF/synchronization; platform/firmware/operational
boundaries. Only the executor prepared the documentary reconciliation.
It does not apply patches, change the profile, approve the proposed skill
contract or repair the implementation issues identified below.

## Evidence and baseline

Use `STATIC_CONFIRMED` for inspected source/inputs, `HISTORICAL_REPORT` for
earlier test reports not reproduced or independently checked here, and
`UNKNOWN` for missing facts. Keep source evidence, binary identity, build,
execution, stability and performance separate.

- Clean Mesa `27.0.0-devel`, commit
  `13baeb70c066a9f82d2bcfb29f06e4865212affa`; project HEAD
  `b64d2fb10e191a8f5666bb509a27b4422df6030f`.
- Current input ID, recomputed and matching [sources.lock](../../../sources.lock:7):
  `sha256:3e20d28a3753e671f6cbfe164372e71b55ecf407dec039f56c05232c53bf2060`.
- This hash includes patches and overlays, including experimental inputs;
  it does not identify which variant was applied. Require the per-artifact
  manifest, ABI, variant, Build ID and ICD SHA-256 for runtime claims.
  See [compute-patch-series-id.py](../../../scripts/compute-patch-series-id.py:54)
  and [build_provenance.py](../../../scripts/build_provenance.py:26).
- Kraid is present in clean Mesa and conditionally linked with
  `with_panfrost_rust`. Treat migration as the plan's completed architectural
  decision, not a reason to reopen compiler analysis.
- The clean Mesa kmod source list does not contain Kbase. Default selected
  families are `common → android → kbase-common → app-loader → wsi → csf →
  csf-v11`; each family's overlay is copied after its patches. An overlay
  alone is not a reconstructed final tree. Experimental sync 002–004 remains
  opt-in, without 001, only for `g615-v11-csf`.
  See [apply-patches.sh](../../../scripts/apply-patches.sh:27).

Existing E-001–E-014, FND and RSK identifiers are preserved. Their old
modified-checkout observations are historical, not current baseline facts.
Canonical F0–F5 definitions remain unavailable; the domain map below must
not be presented as reconstructed phase completion.

## Kbase UAPI and CSF

The backend overlay consumes
[mali_kbase_ioctl.h](../../../patches/kbase-common/files/include/drm-uapi/mali_kbase_ioctl.h:28).
Reference headers with similarly named structures do not establish the
actually used ABI. Request identity includes type, direction, number and
size, not just an ioctl name or UAPI version string.

For the reported Moto CSF 1.21, patch 110 statically selects:

| Operation | Predicted candidate order | Qualification |
|---|---|---|
| Queue-group create | 32 → 112 → 40 bytes; nr 42 then nr 58 | Source selector, not observed Moto requests |
| Tiler-heap init | 16 → 24 bytes; nr 48 | Source selector, not accepted-layout proof |
| Memory allocation | MEM_ALLOC_EX, nr 59 / 64 bytes; restricted legacy nr 5 / 32-byte fallback | No current allocation execution |

Source: [patch 110](../../../patches/csf-v11/110-select-kbase-csf-uapi-layouts-and-16k-pages.patch:450),
including selectors at lines 524–558. Group/heap fallback advances only on
EINVAL/ENOTTY and caches the accepted layout per device. ENOMEM, EPERM and
EACCES are not reasons to force another ABI. For 1.21, fault-report enable
remains false; accepting a larger structure does not prove support for future
fields. Historic host/layout tests and the G57 JM allocation run remain E-012,
not Moto CSF or 16 KiB validation.

Lifecycle to trace: VERSION_CHECK_CSF → SET_FLAGS/tracking → GLB interface
query → group → ring REGISTER → BIND cookie → three CPU-page USER_IO mapping
→ publication/doorbell or KICK → notifications/completion → queue/group TERM.
Cookie and GPU VA are distinct. CPU-page size is not the GPU MMU granule.
The driver uses a group per subqueue and CSI0; MC2 does not imply two CSI.
Sources: [backend overlay](../../../patches/kbase-common/files/src/panfrost/lib/kmod/kbase_kmod.c:691),
[queue patch 007](../../../patches/csf/007-gpu-queue-kbase.patch:1013),
[page handling in 110](../../../patches/csf-v11/110-select-kbase-csf-uapi-layouts-and-16k-pages.patch:287).

Preserve the first kernel-wrapper error: publication may log KICK failure
without propagating its return. Group faults latch device error; no automatic
recovery is established. Heap TERM is separate from queue/group TERM.
Event signal nr 44 is `_IO` without payload; patch 111 logs notification
failure without returning device-lost from event operations. VK_SUCCESS from
SetEvent does not prove notification delivery.
Sources: [085](../../../patches/csf-v11/085-keep-descriptor-ring-and-vkevent-syncs-in-csf-event-memory.patch:22),
[111](../../../patches/csf-v11/111-never-return-device-lost-from-set-reset-event.patch:39),
[backend notifications](../../../patches/kbase-common/files/src/panfrost/lib/kmod/kbase_kmod.c:604).

Historical 110 dependencies on JM are not a reason to restore JM today.
Patch 237 carries shared EXEC-before-JIT/page-size changes; current 118 does
not contain the backend hunks described as conflicting in the old worklog.
This is selection/source reconciliation, not replay validation.
See [237](../../../patches/csf-v11/237-kbase-exec-jit-and-ion-compatibility.patch:64)
and [118](../../../patches/csf-v11/118-log-kbase-and-device-decisions.patch:16).

## Memory and synchronization

### Critical static discrepancy: SAME_VA versus NEED_MMAP

The [overlay README](../../../patches/kbase-common/files/README:12) documents
the historical “011” correction: NEED_MMAP-only import should retain the
returned GPU VA; only SAME_VA should use the cookie/mmap relationship.
However, the examined
[import code](../../../patches/kbase-common/files/src/panfrost/lib/kmod/kbase_kmod.c:1512)
still sets `same_va` from `(SAME_VA | NEED_MMAP)` and line 1542 always uses
the CPU mapping as GPU VA. No correcting later import post-image was
identified in the targeted patch investigation.

**FAIL of static consistency**, not a reproduced Moto failure. Conditional
on NEED_MMAP without SAME_VA, the wrong classification also controls cleanup
and omission of explicit MEM_FREE. Actual Moto outflags and kernel lifetime
are unknown. Do not claim the documented correction is applied or that every
import fails. A source fix and focused success/error cleanup tests are a
separate authorized implementation task.

### Cache, allocation and ownership

DMA-BUF memory import/export duplicates FDs with CLOEXEC. Placed mappings use
shared backing; a BO without suitable DMA-BUF backing cannot safely obtain
placed mapping through an invented shadow-copy fallback. Restrict MAP_FIXED
to a range reserved by the test itself.
See [BO import/map/cache paths](../../../patches/kbase-common/files/src/panfrost/lib/kmod/kbase_kmod.c:1452)
and [placed memory patch 091](../../../patches/csf-v11/091-allocate-placeable-host-memory-from-the-dma-heap.patch:38).

SAME_VA, NEED_MMAP, alias, EXEC/JIT zone initialization and Vulkan sparse
are distinct contracts. EXEC/JIT VA reservations are not physical allocations.
Keep Vulkan sparse gated; internal alias/TLS mechanisms do not prove sparse
feature support. No new sparse investigation is needed for skill generation.

Per-BO coherent outflags may suppress MEM_SYNC; they do not eliminate
execution barriers, fences or lifetime obligations. `bo_wait` in the overlay
does not wait on a BO fence. DMA_BUF_IOCTL_SYNC, Kbase cache maintenance and
sync_file completion are separate mechanisms. A valid/readable fence FD alone
does not prove content correctness or coherency.
See [cache/BO wait](../../../patches/kbase-common/files/src/panfrost/lib/kmod/kbase_kmod.c:1833)
and [opt-in coalescing 003](../../../patches/experimental-kbase-sync/003-kbase-coalesce-mem-sync.patch:16).

### Residual synchronization defects and unknowns

| Concern | Static finding / boundary |
|---|---|
| Waiter lifetime | Default successful wait loses the waiter pointer without freeing it; experimental 004 supplies frees, only opt-in. Concurrency still depends on external synchronization. |
| CLOEXEC | Sync-file import/re-export uses `dup`; unlike memory-FD duplication, it does not preserve CLOEXEC. Lifetime patch 004 does not fix that. |
| Deadline / EINTR | Poll reuses its original interval on EINTR/EAGAIN; conversion truncates sub-ms and lacks a clamp for long durations. It does not enforce an absolute total deadline. |
| Poll events | Existing logic does not reject POLLNVAL or require POLLIN before reporting completion. Historical simple PASS cases do not cover it. |
| Partial KCPU enqueue | Export uses separate wait and signal ENQUEUEs. A successful first enqueue followed by failure does not establish rollback/cancellation; kernel semantics and later queue state are unknown. |
| Cross-queue fallback | Experimental 002 commits staged userspace targets only if they fit; external sync_file and unsupported cases retain CPU fallback. It does not repair partial KCPU enqueue or FD/poll defects. |

Sources:
[default sync implementation](../../../patches/kbase-common/004-physical-device-kbase.patch:475),
[poll and waiter import](../../../patches/kbase-common/004-physical-device-kbase.patch:608),
[export patch 075](../../../patches/csf-v11/075-export-kbase-sync-file-fences-through-a-kcpu-queue.patch:29),
[opt-in lifetime 004](../../../patches/experimental-kbase-sync/004-kbase-sync-file-waiter-lifetime.patch:44),
[opt-in release 002](../../../patches/experimental-kbase-sync/002-android-release-queue-mesa27.patch:179).

These findings need explicit limits in the skill, not silent promotion of
experimental fixes or implementation changes in this documentary task.

## Android versus Linux/glibc

| Dimension | Android/Bionic | Linux/glibc chroot |
|---|---|---|
| Userspace | Android app/hot-load and Android loader/WSI | glibc application, glibc Vulkan loader, glibc ICD and ICD JSON |
| Kernel | Moto Android Kbase; CSF 1.21 reported | Same handset kernel, not Linux-native/Panthor |
| Build inputs | NDK target dependencies; host generators remain host | GNU/AArch64 target dependencies and guest libc/loader must match |
| Access | App, shell and root/KSU are different contexts | Guest filesystem view does not grant device, socket or SELinux access |
| WSI | Driver-owned buffers, external AHB and private ANB release are distinct gates | Headless does not test X11/Wayland presentation; verify compositor/socket access separately |
| Evidence | Narrow historical Moto cases, identified below | Moto runtime qualification not recovered in the consulted sources |

Sources: [architecture](../../ARCHITECTURE.md:3),
[G615 specification](../../superpowers/specs/2026-11-21-g615-only.md:3),
[Android build](../../../scripts/build-android.sh:20),
[glibc build](../../../scripts/build-glibc.sh:86).
Compilation API, device API and package minApi are separate values.
The build scripts are not permission to invoke their setup/chroot operations.
Confirm the actual guest is glibc; a wrapper name does not establish its libc.
Confirm the loaded private ICD and marker precedence, not only a ZIP hash.
See [test loader](../../../tests/android-loader-app/jni/panvk_loader_test.c:28).

The build profile still names Poco MC6. Preserve it as an existing build
input; do not copy its core mask, kernel, node permissions or `glibc: pass`
into the Moto inventory. Profile modification needs separate approval.

## Historical Moto evidence and deferred AHB

| Record | Binary / series | Reusable result, not current qualification |
|---|---|---|
| E-016 initializer manifest | `c4532ef9...` / `7d02a194...` | Targeted workloads; explicitly excludes full CTS, Android presentation and AHB |
| E-017 AHB/WSI/sync investigation | `a273db7e...` / historically `a06b...` | Driver-owned WSI draw 300/300 and two app sync modes reported PASS |
| E-017 external-AHB app import | same historical candidate | `FAIL (deferred)` during metadata/layout lookup before DMA-BUF import |
| E-018 native-buffer release | prior `3e79dd98...` versus candidate `d30b7c60...` | Shell release results differ; app image creation fails before release, so app release is untested |

See [initializer manifest](../../../validation/mesa27-large-draw-initializer-fix.json:4),
[AHB results and decision](../../superpowers/plans/2026-11-22-ahb-app-uid-investigation.md:97),
[native-buffer diagnostic](../../../tests/README.md:250).
The original raw-manifest association for `a273...` remains incomplete.
None of these hashes identifies the current `3e20...` input state.

Do not reopen AHB causality: the documented ROM denies mapper/metadata access
in the app context. A privileged control is not equivalent. Do not alter
SELinux/linker policy or extend the cookie-writing probe to externally owned
buffers. Revisit only by user decision or a new release requirement.

## Operational boundaries and backlog

Before a future authorized run, identify device, process context, libc/ABI,
selected variant, binary/manifest and page size. First reuse matching logs;
new hardware collection still requires approval. Missing/denied properties
remain UNKNOWN, not a request to elevate privilege or change permissions.

Do not attach a second notification reader to the driver's FD, invent raw
ioctl layouts or force ABI fallback on resource/access errors. Use a small
workload, a total timeout and an approved mechanism that stops the actual
target process. A host/ADB timeout alone may leave remote work running.
Do not substitute the long CTS resume runner for a bounded diagnostic.
See [CTS runner](../../../scripts/dxvk/cts-resume.sh:194).

Stop on first inconsistent VA/outflags, cache/ioctl error, wrong readback,
POLLNVAL, FD growth, unexpected timeout, total-deadline expiry, device-lost,
kernel fault, unresponsive system or thermal/data risk. A fixture's explicitly
expected timeout and serial wait are test stages, not failed-attempt retries.
Preserve the first error and binary identity.
No automatic GPU reset, reboot, clock/governor/firmware write, broad process
termination, policy change or cleanup of preexisting files.

Firmware identity, DDK/kernel details, page size, GLB facts, energy/DVFS,
suspend/resume and recovery remain UNKNOWN where matching Moto evidence was
not recovered. Kernel source absence does not prevent a limited skill; it
prevents claims about unobserved handlers and firmware behavior.

| Priority | Next action / exit |
|---|---|
| P0 documentation | Proposed reconciliation and evidence-ID corrections; keep original audit and historical IDs |
| P1 separate implementation | SAME_VA/NEED_MMAP import discrepancy, waiter lifetime, CLOEXEC, deadline/revents and partial-enqueue error handling; require authorized fixes and focused regression tests |
| P1 qualification only | Obtain matching manifest/logs for each ABI/variant before claiming current runtime compatibility; glibc/Moto remains unqualified |
| P2 residual | Recover canonical F0–F5 index, raw candidate manifest, kernel/firmware/page/GLB details when available; do not block skill drafting |
| Deferred | External-AHB app import on the documented ROM; no automatic reinvestigation |
| Next stage | Generate the proposed skill, references and workflows with these limits; independent audit occurs after integration, not per document |

## Verification and disposition

| Gate | Result |
|---|---|
| Clean Mesa and current-series computation | PASS, read-only checks |
| Targeted source/selection investigation | PASS documentary; no application or runtime inference |
| SAME_VA/NEED_MMAP consistency in examined inputs | FAIL, static discrepancy; source fix not performed |
| Exact current Moto Android/glibc runtime qualification | BLOCKED by missing matching artifact/evidence |
| Internal kernel/firmware behavior | UNKNOWN; source unavailable, not a documentary-generation blocker |
| Documentary structure and references | PASS: 10 documents, 91 local links/locators, anchors, E-001–E-021 and unchanged historical audit checked |
| Documentary patch whitespace, scope and applicability | PASS: nine intended document paths; `git diff --check` and `git apply --check --whitespace=error -v` succeeded without offsets/fuzz; no patch application |
| Full downstream Mesa replay, build, assertions, functional/hardware/stability/performance tests | NOT EXECUTED |
| Skill generation and independent audit | NOT EXECUTED in this stage |

**Stage 2 disposition: PARTIAL technically, ready for limited skill drafting.**
Critical unknowns and static discrepancies are documented, not repaired or
homologated. Preparing this patch does not authorize applying it or changing
the proposed contract. Historical runtime results remain historical.
