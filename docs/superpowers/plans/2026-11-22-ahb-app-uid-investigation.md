# AHardwareBuffer App-UID Import Failure Investigation Plan

> **For agentic workers:** Investigate the existing app-UID `vkAllocateMemory`
> failure before proposing a driver fix. Keep all tests isolated; do not modify
> the system driver, SELinux policy, protected source trees, or project sources
> without explicit authorization.

**Goal:** Identify the first PanVK/Android layer that causes the candidate ICD's
AHardwareBuffer image import to return `VK_ERROR_INVALID_EXTERNAL_HANDLE` in
the app UID while the ADB-launched Gate G control passes.

**Architecture:** Compare the same candidate ICD and AHardwareBuffer inputs,
while recording the actual process security contexts. Trace the app's
dedicated-image import through PanVK, shared Vulkan Android helpers, gralloc
metadata lookup, and dma-buf import; distinguish the app sandbox from the
root/KSU context used by the current ADB shell.

**Tech Stack:** Android 16/API 36, ADB, Vulkan Android Hardware Buffer and
external-memory APIs, Mesa/PanVK, Android gralloc and SELinux diagnostics.

**Spec:** Observed evidence is in the session artifacts `wsi-draw-full-app.log`,
`uid-ahb-investigation-logcat.log`, and `ahb.log`. The app reports AHB
properties (`allocationSize=16384`, `memoryTypeBits=0x3`) and fails its
dedicated `vkAllocateMemory` with `-1000072003`; the ADB-launched control
imports, renders, reads back, and releases its AHB.

## Global Constraints

- Target only device `ZF525GRGXD`, Mali-G615 MC2, Android 16/API 36, profile `g615-v11-csf`.
- Keep candidate ICD SHA-256 `a273db7ea158c5316fb63777c3712f7a13b1df970efab3b237e869be30c2c167` fixed across comparisons.
- Treat `work/mesa/` as read-only; no system driver, permissions, SELinux, or device configuration changes.
- `adb shell` currently runs as `uid=0`, SELinux context `u:r:ksu:s0`; do not label it an ordinary Android shell UID.
- Trace the candidate against the read-only snapshot `.../files/g615-build-android-candidate/mesa-final2-default/`, not the current `work/mesa/`. The historical build record associates this ICD with patch series `a06b...`; the current checkout's `2657...` is a different state.
- Preserve Gate H's independent `300/300 (draw)` result; do not conflate it with Gate G.
- Do not apply a Mesa patch or build an instrumented driver until the failing subcall is identified and the user authorizes source changes.

## Review Focus

- **Caller identity:** app UID, process SELinux context, device vendor API, and ROM may differ from shell; record these before interpreting results.
- **AHB allocation versus import:** successful allocation and properties query do not prove that the image-layout or dma-buf import path succeeded.
- **Generic Vulkan error:** `VK_ERROR_INVALID_EXTERNAL_HANDLE` can represent gralloc metadata, memory-type compatibility, or dma-buf import failures; identify the returning subcall.
- **Mapper hypothesis:** prior stock MediaTek devices logged `mapper/mediatek` access denied, but that is not proof for this handset or this candidate build.
- **Input parity:** compare the AHB descriptor, dedicated-image pNext chain, allocation size, and selected memory type before changing any variable.

---

### Task 1: Reconfirm the controlled baseline

**Files / evidence:**
- Read: session artifact `wsi-draw-full-app.log`
- Read: session artifact `ahb.log`
- Read: `tests/android-loader-app/jni/panvk_loader_test.c`
- Read: `tests/ahb/ahb.c`

- [x] Record the device build fingerprint, vendor API level, board platform, SELinux mode, isolated app UID, and current ADB shell identity using read-only queries.
- [x] Confirm the candidate ICD hash in the shell binary and the app APK, and compare the AHB descriptor, `allocationSize`, `memoryTypeBits`, dedicated image chain, and chosen memory type.
- [x] Produce an app-versus-ADB-control comparison; mark the shell run's unrecorded runtime identity as a limitation rather than assuming it.

**Expected result:** A reproducible baseline that separates established input parity from remaining unknowns.

### Task 2: Trace the error to its first failing implementation layer

**Files:**
- Read-only candidate snapshot: `.../files/g615-build-android-candidate/mesa-final2-default/`
- Read: `src/panfrost/vulkan/panvk_android.c`
- Read: `src/vulkan/runtime/vk_android.c`
- Read: `src/util/u_gralloc/u_gralloc_fallback.c`

- [x] Follow the dedicated AHB image import through layout discovery and error propagation in the candidate source snapshot; establish whether execution reaches dma-buf memory-requirement calculation.
- [x] Map the observed `VK_ERROR_INVALID_EXTERNAL_HANDLE` to the metadata/layout return path and distinguish it from earlier fd lookup or later memory-import returns.
- [x] Confirm that the dedicated image path invokes `vk_android_get_ahb_layout()` / `u_gralloc_get_buffer_basic_info()` after AHB properties were queried successfully.

**Expected result:** The first failing return site is confirmed and separated from later fd/memory-import failures.

### Task 3: Capture app-UID Android and Mesa diagnostics

- [x] Re-run only the isolated Gate G/WSI app test with the candidate APK and ICD; capture `adb logcat -b all -v threadtime` around that process without clearing existing logs.
- [x] Filter the captured log for `PanVK`, `MESA`, `ServiceManagerCppClient`, mapper, linker-namespace, and SELinux `avc: denied` messages.
- [x] Record the app process UID/context and read-only device properties alongside the failure timestamp.

**Expected result:** Either a concrete app-namespace/mapper denial or evidence that the failure occurs later in fd/memory import; absence of a log is not proof that a path succeeded.

### Task 4: Run one-variable discriminating checks

- [x] Confirm the app-process mapper lookup denial and compare it with the passing ADB-launched control without changing SELinux or linker policy. The current ADB shell identity is root/KSU, not ordinary UID 2000.
- [x] Stop before fd/memory-import comparisons: the observed layout lookup fails before the image memory-requirement and dma-buf import steps.
- [x] No Vulkan inputs were varied; process context is the observed distinguishing factor, although the earlier control run did not record its identity at run time.

**Expected result:** A confirmed first failing subcall and a minimal distinguishing condition, or an explicit unresolved boundary if existing logging is insufficient.

### Task 5: Report the cause and propose the smallest next action

- [x] Report facts separately and distinguish the root/KSU ADB Gate G control, app-UID Gate G, and Gate H WSI.
- [x] No source instrumentation is needed to identify the first failing call; exact binary-to-patch-series provenance remains unresolved.
- [x] Do not recommend a mapper, SELinux, or driver workaround from this evidence. Any later authorized change must pass app-UID Gate G; do not broaden the cookie-writing linear probe to externally owned AHBs.

## Investigation Results

### Device and comparison

| Input / result | App Gate G | ADB-launched Gate G control |
|---|---|---|
| Device | moto g86 5G, `mt6878`, vendor API 34, Android API 36, SELinux Enforcing | Same device |
| Build fingerprint | `motorola/nice_g_sysn/nice:16/W1VNS36H.60-82-8/3b3952-002b7a0:user/release-keys` | Same device |
| Process context | UID 10432, `u:r:untrusted_app:s0:c176,c257,c512,c768` | The current `adb shell` reports UID 0, `u:r:ksu:s0`; the earlier Gate G log did not record its identity at run time |
| ICD | Candidate SHA-256 `a273db7e...c2c167`; verified inside the candidate APK | SHA-256 `a273db7e...c2c167` |
| AHB | 64x64, one layer, RGBA8, stride 64, usage `0x203`; allocation size 16384, memory bits `0x3` | Test source uses the same 64x64 RGBA8, GPU-color-output + CPU-read usage; log records stride 64, allocation size 16384, bits `0x3`, chosen type 0 |
| Dedicated import | Fails `vkAllocateMemory` with `-1000072003` | Import, render, and readback pass |

### Confirmed failure path

The app log records SELinux `find` denials for `mapper/mediatek` and
`mapper/common`, plus the app linker's refusal to load `mapper.mediatek.so`
from namespace `clns-9`. Mesa then reports that complete gralloc metadata is
unavailable (`rc=-95`) and `u_gralloc_get_buffer_basic_info` fails.

In the candidate source snapshot, the dedicated-image path calls
`panvk_android_ahb_image_init()` and `vk_android_get_ahb_layout()`. The
gralloc-layout query returns `VK_ERROR_INVALID_EXTERNAL_HANDLE`. The subsequent
`cpu-linear-probe` is deliberately limited to the AHB currently owned by
PanVK's WSI path; an externally allocated AHB such as Gate G's is rejected
before the probe writes any cookies. Thus the failure occurs during
layout/metadata discovery, before image memory-requirement calculation and
dma-buf import. Gate H remains independently approved at 300/300 draw cycles:
its driver-owned swapchain buffers can use the linear probe.

The passing ADB-launched test is a privileged control, not evidence that an
ordinary app or UID-2000 shell can access the mapper. Its successful external
AHB import is consistent with mapper access in the privileged context, but the
shell run did not capture a successful mapper log.

### Provenance limitation and next action

The runtime log strings match the read-only `mesa-final2-default` source
snapshot (base commit `13baeb70c066a9f82d2bcfb29f06e4865212affa`), but that
snapshot has local modifications. Checkpoint 006 records this ICD hash
(`a273db7e...c2c167`), Build ID
`2022397a6ebdeba3cde351ee34119cc12b8a31c2`, manifest SHA-256
`8fbf0d532c93119626c20e87f2ba6d5328b77fd107badae7ee3c359aad7e6cf1`, and
patch-series ID `a06b008393c73f99a80939cf5f3ce4a1ee1b0bf30d697aa3e3fde85b51dedeaa`.
Recomputing the candidate tree's patch-series ID also yields `a06b...`.
However, the current checkout computes `2657...`, and the candidate artifact's
`sources.lock` also says `2657...`; the available initializer-fix manifest is
for a different binary (`c453...`) and series (`7d02...`). The raw manifest
whose hash is recorded in checkpoint 006 was not found. Treat `a06b...` as the
documented provenance of the tested ICD, but do not equate that candidate with
the current `2657...` checkout.

The documented [Android NDK AHardwareBuffer API](https://developer.android.com/ndk/reference/group/a-hardware-buffer)
provides buffer descriptions and CPU locking/plane strides, but this does not
provide a safe DRM modifier and plane-layout query for importing an opaque
external dma-buf. In this ROM, the app cannot reach the vendor mapper that
provides those gralloc metadata. Consequently, the safe resolution for Gate G
is a platform/OEM-supported metadata path accessible to the app/driver context;
without one, keep external-AHB import blocked on this ROM. Gate H remains a
separate passing path. Do not alter SELinux, linker policy, or system files,
and do not let the cookie-writing probe modify externally owned AHBs.

### User decision

On 2026-11-22, the user deferred resolving app-UID external-AHB import and
confirmed that it is not a current migration blocker. Continue with the next
independent validation item; retain Gate G app-UID as `FAIL (deferred)` for
this ROM and do not claim external-AHB import support. Revisit the platform
metadata path when the user requests it or when that capability becomes a
release requirement.

### Follow-up: Android synchronization validation

On 2026-11-22, ran both synchronization modes in the temporary
`org.panvk.loadertest` APK on the moto g86 5G (Mali-G615 MC2). The process was
confirmed as app UID 10433 in `u:r:untrusted_app:s0:c177,c257,c512,c768`.
Both modes loaded ICD SHA-256
`a273db7ea158c5316fb63777c3712f7a13b1df970efab3b237e869be30c2c167`; its
historical patch-series association is `a06b...`, not the current checkout's
`2657...`.

| Test mode | Result | Hardware evidence |
|---|---|---|
| `sync_fd` | **PASS** | Queue submit and `vkGetSemaphoreFdKHR` returned success; the exported sync-file passed `SYNC_IOC_FILE_INFO`, became poll-readable within the bounded wait, and the fence wait returned success. |
| `sync_wait_signal` | **PASS** | Initial signal submit and separate `vkQueueSubmit2` wait-and-signal submit returned success; exported sync-file validation, bounded poll, and fence wait all succeeded. |

Each mode was launched separately with `am start -W` after force-stopping the
test package:

- `adb shell am start -W -n org.panvk.loadertest/org.panvk.loadertest.MainActivity --es test_mode sync_fd`
- `adb shell am start -W -n org.panvk.loadertest/org.panvk.loadertest.MainActivity --es test_mode sync_wait_signal`

PID-filtered logs were preserved in the session artifacts.
Both activities reported result `0`; neither launch timed out. The evidence
covers these synchronization cases only on this device and this candidate ICD.
It does not validate external-AHB import, WSI, a rendered workload, or other
profiles/devices, and it does not change Gate G's `FAIL (deferred)` status.
