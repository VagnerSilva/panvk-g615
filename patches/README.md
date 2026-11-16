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
- `kbase-common/` — pan_kmod/Kbase abstraction shared by JM + CSF.
- `csf/` — CSF queue/group/register/bind/kick lifecycle (all CSF).
- `csf-v10/ csf-v11/ csf-v12/ csf-v13/ csf-v14/` — arch-scoped CSF quirks.
- `jm-v7/` — Bifrost v7 JM backend.
- `jm-v9/` — Valhall v9 JM backend (a real port, not a flag).
- `app-loader/` — generic ICD exports (`vk_icdGetInstanceProcAddr`,
  `vk_icdNegotiateLoaderICDInterfaceVersion`) coexisting with Android WSI.
  The G52 lesson: enabling Android WSI must not select the HAL-only symbol
  scheme and hide the ICD entry points.
- `wsi/` — swapchain/acquire/present/resize, acquire-present sync.

Rules:

- Fail the build if a required patch does not apply (never continue after
  patch drift silently).
- No release from an unrecorded Mesa commit (`sources.lock` is normative).
- P3 rebase target: pinned Mesa in `sources.lock` (27.0.0-devel/main).

Mesa 27 migration (in progress):

- CSF v11 backports 026-031 and 033-037 are already implemented in the pinned
  Mesa 27 base and are no longer part of the active series. This includes the
  indirect-draw FAU flush, v11 architecture cases, presentation extensions,
  modifier capability queries, and image compression controls.
- Patch 032 retains only the downstream optimal-only BC modifier restriction;
  its upstream modifier-query implementation is already in Mesa 27.
- Patch 187 retains only downstream Vulkan naming; Mesa 27's distinct
  G725/G925 model rows and feature-based selection are preserved.
- The complete `g615-v11-csf` series (218 patches, including JM v9/v7) passed
  `scripts/apply-patches.sh` without offsets or fuzz in a new detached worktree
  at `13baeb70c066a9f82d2bcfb29f06e4865212affa`. Existing source and build
  directories were not reused. This verifies patch applicability, not API
  compatibility or runtime correctness.
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
  The profile also applies jm-v9 023, whose tiler-heap call already has a label.
- The geometry-shader passthrough varying calls use `inputs.arch` for Mesa 27;
  patch 076's dependent context was updated. The viewport calls introduced by
  patch 090 are already converted to `inputs.arch` by jm-v9 011 in this profile.
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
