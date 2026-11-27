# Architecture

```text
Android app (Samba S3 / loader-test APK)
 -> libvulkan_panfrost.so (Bionic, hot-loadable ICD)
    -> generic ICD exports (vk_icdGetInstanceProcAddr, vk_icdNegotiateLoaderICDInterfaceVersion)
    -> Android WSI (VK_KHR_android_surface + swapchain)
    -> AHardwareBuffer / gralloc external-memory interop
    -> PanVK core (Mesa main / 27.0.0-devel + patch series)
    -> pan_kmod Kbase backend (CSF queue/group/register/bind/kick)
    -> Kbase CSF ioctls -> /dev/mali0 -> Mali-G615
```

glibc path:

```text
glibc Vulkan app (Bachata S4 / NativeCode)
 -> glibc libvulkan loader -> glibc libvulkan_panfrost.so + panfrost_icd.aarch64.json
 -> Kbase CSF ioctls -> /dev/mali0 -> Mali-G615
```

Only PanVK v11 is compiled. Discovery additionally requires the G615 product
and an actual Kbase CSF context; other products and JM contexts are rejected
before device exposure. Both targets use `-Dpanfrost-kmds=kbase`.
Upstream compiler and GPU model infrastructure remains available, but it is
not a promise of support for another GPU.

The 38 downstream JM patches have been removed. Patches 235-240 preserve the
shared model/budget API, viewport varying architecture, EXEC/JIT page sizing,
ION fallback, XCB symbols and draw-chunk instance cap. Kbase sync
002-005 is included by default following user approval on 2026-11-24.
The separately approved sync_file poll correction 007 follows 005; it
validates poll events and recomputes finite deadlines without changing
the WAIT_ANY backoff or sync ownership.
Historical app binaries and runtime evidence are not
relabelled as this candidate.

Key lessons carried forward:

- Kbase sync != DRM syncobj. Output semaphores signal through the active
  `vk_sync` type (G52 output-semaphore fix).
- Android WSI must coexist with generic ICD symbols; a HAL-only symbol scheme
  hides `vk_icdGetInstanceProcAddr` (G52 Android-platform issue).
- Never guess `native_handle_t->data[0]` as the dma-buf; use the real
  gralloc/AHB metadata path. Never map a missing DRM modifier to LINEAR.
- Valhall v9 is a backend port, not a build flag.
- Synchronous Kbase submission first; async only after correctness.
