# Patch families

Every patch file must carry a header:

```text
Purpose: ...
Source/Reference: <url + commit>
Tested GPU: ...
Tested Kbase UAPI: ...
Mesa base range: ...
Dependencies: ...
Validation test: ...
```

Directories:

- `common/` — upstream-safe fixes, build fixes, logging.
- `android/` — Bionic/NDK build, Android WSI, gralloc/AHB interop.
- `kbase-common/` — pan_kmod/Kbase abstraction used by the G615 CSF build.
- `csf/` — CSF queue/group/register/bind/kick lifecycle (all CSF).
- `csf-v11/` — the active G615 architecture-scoped patches.
- `app-loader/` — generic ICD exports (`vk_icdGetInstanceProcAddr`,
  `vk_icdNegotiateLoaderICDInterfaceVersion`) coexisting with Android WSI.
  The G52 lesson: enabling Android WSI must not select the HAL-only symbol
  scheme and hide the ICD entry points.
- `wsi/` — swapchain/acquire/present/resize, acquire-present sync.
- `experimental-kbase-sync/` — historical directory name for the Mesa 27 G615
  sync updates promoted to the default series on 2026-11-24. Preparation
  appends exactly 002, 003, 004 and 005 after `csf-v11/`; historical 001 and
  any unlisted patches remain excluded. `--with-kbase-sync` is retained for
  compatibility, not required. See the family README for user approval,
  validation results and the unresolved shutdown limitation.
  Draft 006 contains the inactive UAPI/Kmod import bridge and a
  mutex-protected CLOEXEC sync-file snapshot helper. It is not selected
  and does not provide a complete GPU wait path.

The historical `jm-v7-wip` patch files are not part of the selected Mesa 27
G615 series and have been removed from this tree. Its README and worklogs
remain historical records. The old universal tree cannot be reconstructed
from this checkout; the universal and v9 preparation scripts are retired.
The remaining 38 `jm-v9`/`jm-v7` patches have also been retired. Their
[inventory](../docs/engineering/g615-patch-inventory.tsv) records the shared
dependencies extracted into 235-240 and the evidence for dropping each
legacy implementation. Other architecture families are not selected.

The G615-only series contains 196 patches by default, including sync
002-005. PanVK builds only v11 and checks the actual Kbase CSF context in
addition to the G615 product ID. The six replacement patches follow their
late v11 prerequisites: Kbase/model APIs (235), varying architecture (236),
EXEC/JIT and ION (237), build/discovery policy (238), XCB symbols (239), and
the shared draw-chunk instance cap (240).

`kbase-common/018` supersedes the unconditional physical backend build in
`kbase-common/002`: `panfrost-kmds` now controls both compilation and
registration. The Panfrost source remains available when virtio is enabled.
Changing this series changes its provenance; validate each affected target
independently.

Rules:

- Fail the build if a required patch does not apply (never continue after
  patch drift silently).
- No release from an unrecorded Mesa commit (`sources.lock` is normative).
- P3 rebase target: pinned Mesa in `sources.lock` (27.0.0-devel/main).

Historical Mesa 27 migration checkpoints (before JM retirement):

- Android patch 018 ports the native-buffer dma-buf fd search from historical
  `jm-v7-wip/0178` to the main series.
- CSF v11 backports 026-031 and 033-037 are already implemented in the pinned
  Mesa 27 base and are no longer part of the active series. This includes the
  indirect-draw FAU flush, v11 architecture cases, presentation extensions,
  modifier capability queries, and image compression controls.
- Patch 032 retains only the downstream optimal-only BC modifier restriction;
  its upstream modifier-query implementation is already in Mesa 27.
- Patch 187 retains only downstream Vulkan naming; Mesa 27's distinct
  G725/G925 model rows and feature-based selection are preserved.
- Before adding the G615-only filter, the `g615-v11-csf` series (218 patches,
  including JM v9/v7) passed `scripts/apply-patches.sh` without offsets or fuzz
  in a new detached worktree at `13baeb70c066a9f82d2bcfb29f06e4865212affa`.
  At that checkpoint the G615-only filter was `csf-v11/234`, immediately after 233 and before JM.
  That series strictly replayed as 224 patches, or 227 with opt-in
  Kbase sync 002-004. These checks prove applicability, not build or runtime.
- Ports preserve upstream poly heap state, Android external-format-resolve
  preprocessing, X11 event connections, named BO allocations, and TLS size
  copies. Fork handlers also acquire Mesa 27's queue `finish_lock` before the
  queue lock, following the upstream finish/teardown lock order.
- Historical device-test metadata in patches describes the earlier Mesa base,
  not validation of the Mesa 27 port.

Build validation checkpoint (isolated native Linux build, not Android):

- Meson setup with `-Dpanfrost-kmds=kbase` passed.
- Native `mesa_clc`, `vtn_bindgen2`, and `panfrost_compile` compiled after
  fixing the fork patch's explicit CPU-detection include and the buffer-texture
  lowering patch's architecture argument.
- `kbase_kmod.c` and `libpankmod_lib.a` compile with the seven-argument
  `pan_kmod_dev_init` call, allocator before operations, and explicit failure
  cleanup. The overlay supplies `kbase_sync_provider.h`.
- The provider is a non-DRM capability boundary, not a new GPU synchronization
  implementation: Kbase has no DRM syncobj handle namespace. Every syncobj
  operation reports `EOPNOTSUPP` and logs the unsupported operation; timeline
  callbacks remain NULL. No fake handles, DRM ioctls or success stubs are used.
  Existing PanVK `kbase_cpu_sync_type`, queue completion targets, software
  timelines and KCPU fence exports remain responsible for synchronization.
- Provider clones share an immutable table with an atomic reference count;
  finalizing the kmod owner does not invalidate a logical-device clone.
  Host tests cover allocation failure, concurrent clone/finalize, explicit
  unsupported errors and unchanged output parameters/fd ownership.
- The five surviving unlabeled `panvk_priv_bo_create` calls now pass descriptive
  labels. Calls subsequently converted to `panvk_priv_bo_create_kind` retain
  their existing labels; patch 205's context was refreshed for the arena label.
- A new detached Mesa worktree at the pinned commit replayed all 218 patches
  with `scripts/apply-patches.sh --profile g615-v11-csf` without offset or fuzz.
  That historical profile also applied jm-v9 023, whose tiler-heap call already had a label.
- The geometry-shader passthrough varying calls use `inputs.arch` for Mesa 27;
  patch 076's dependent context was updated. The viewport calls introduced by
  patch 090 were converted to `inputs.arch` by jm-v9 011; replacement 236 now preserves those calls.
- A fresh isolated replay applied all 218 patches without offsets or fuzz.
  Native Meson setup with Kbase passed using existing local Rust subprojects.
  `libpankmod_lib.a`, the v9 and v11 shader objects, and `libpanvk_v11.a` all
  compiled.
- The JM v9 query-kernel guards now include both the existing clear/copy
  kernels and the v9 pipeline-statistics kernel, without enabling the JM
  kernels for CSF. A fresh strict replay applied all 218 patches, and the
  generated headers and query objects were checked for v6, v7, v9, v10 and
  v11.
- Patch jm-v9 032 updates Kbase model selection and memory budget accounting
  for Mesa 27. The heap budget is keyed by the opened Kbase character device
  and released when physical-device initialization fails.
- A new isolated strict replay applied all 219 patches without offsets or fuzz.
  Native Meson setup with Kbase and the complete `libvulkan_panfrost.so` build
  passed. The Kbase sync-provider host test also passed. These checks do not
  establish Android compatibility or device behavior.
- Patch jm-v9 033 adds the Mesa 27 XCB event-connection symbols to the Android
  dynamic loader. A fresh strict replay applied all 220 patches, and an Android
  arm64 build with NDK r30 and the static binary checks passed. The resulting
  development ADPKG is not device-validated.
- Updating the recorded `patchSeriesId` and hardware queue/rendering tests
  remain open.
  The existing provenance identifier is not certification of this patch set.

Mesa 27 Large_Draw initializer correction:

- Common patch 020 defers shader-global initializer lowering until each libpan
  variant has a single entrypoint. The earlier multi-entrypoint pass consumed
  shared zero-array initializers into `panlib_fill` only. Tessellation kernels
  retained their copies without the source initialization.
- The affected `CHWTessellator` flags occupy bytes 32 and 33 of an 80-byte
  object. This is not a 64-byte TLS truncation: triangle `tess_gen` requires
  1,968 bytes and fused count/draw requires 3,520 bytes, rounded to 2,048 and
  4,096 bytes respectively. The pipeline correction preserves those sizes.
- Offline per-pass validation confirms all 80 shared source bytes are
  initialized in both specialized triangle kernels. The explicit two-flag
  diagnostic workaround is not included in the patch.
- The complete 221-patch profile replayed without offsets or fuzz on the pinned
  commit in an isolated worktree.
- The clean pipeline correction passed direct and indirect Large_Draw 8/8
  times at each of 64, 507, 508 and 70,000 patches on Mali-G615 MC2 / Kbase CSF
  1.21 (Android 16). No shader logging, explicit-flag workaround or debug sync
  was used. Full Large_Draw, its separate fan opt-in run (41 cases),
  tessellation, conditional tessellation and XFB standalone tests passed.
  These targeted tests do not establish full Vulkan conformance or validate
  Android presentation/AHB behavior.
- Rebuild the host `panfrost_compile` tool before regenerating libpan kernels.
  Reusing a host-tool cache keyed only by the upstream Mesa commit can retain
  the old compiler even when the patch series changes.
