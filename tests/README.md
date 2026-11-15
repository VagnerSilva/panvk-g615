# Tests

- `kbase-probe/` — Gate B input (P2). C probe, NDK-built, run via adb shell
  AND inside loader-test APK (app UID). Records ROOT/SHELL + TARGET APP UID
  results separately.
- `vulkan-smoke/` — Gates C+D: dlopen, vk_icdGetInstanceProcAddr,
  vkCreateInstance (exact PanVK device, never lavapipe/vendor-accidental),
  vkCreateDevice, queue, mapped buffer, destroy.
- `compute/` — Gate E: 1x1x1 dispatch writing 0x12345678, 10/10 exact.
- `offscreen/` — Gate F: partial-triangle RGBA8 readback (no clear/blit false
  positive), then sampling/depth/stencil/blend/MSAA/MRT/indirect per arch.
- `ahb/` — Gate G: real AHB allocate -> properties -> import -> bind -> GPU
  write -> CPU verify -> release.
- `android-loader-app/` includes Gate H: real ANativeWindow swapchain and
  300-frame presentation. Swapchain resize/recreation is not yet covered.
- `sync/` — fence, binary + timeline semaphores, multi-submit, queue idle,
  acquire/present sync, 300-frame soak, second run.
- `android-loader-app/` — tiny APK proving the release ZIP hot-loads from an
  ordinary app UID (generic dlopen path + AdrenoTools-compat path).
  Its default WSI run needs only the base swapchain path and logs the overall
  and per-swapchain `vkQueuePresentKHR` results. The extra present-id/wait and
  swapchain-maintenance checks can be enabled by creating
  `/data/local/tmp/panvk-test-present-extensions` on the device.
- `runtime-features/` — P10/P11: on-device ICD dump → runtime-feature-matrix.json
  with upstreamImplemented / runtimeExposed / runtimeTested. Parser tests here.
- `features/` — focused advertised-feature workloads. `sync-features.c` covers
  timeline semaphore values/chains and synchronization2 submission/barriers.
- `bcn/` — complete BC1-BC7 compatibility contract and evidence self-check.
  Advertisement is rejected unless every required format, operation, edge case,
  and stress case has `PASS` evidence.
- `dxvk/` — DXVK-only profile, Vulkan semantic, and DXVK Native validation.
  Kept separate from historical combined `dxvk-vkd3d/` evidence.

## Android `vkQueuePresentKHR` diagnostic

The loader APK's default WSI run enables only the base swapchain path, so it
does not require `VK_KHR_present_id2`, `VK_KHR_present_wait2`, or
`VK_KHR_swapchain_maintenance1`. It records the overall `vkQueuePresentKHR`
result and the per-swapchain result for the first five frames, every 50th
frame, and every non-success result. The test renders a changing image to its
`SurfaceView` for 300 frames. If Gate G's AHB import or setup fails, it reports
that failure and attempts Gate H independently using clear-only rendering,
without a graphics pipeline or draw. Passing Gate H in that mode does not
validate draw or shader compilation, and the overall result remains a failure.

The build requires Android SDK platform 35, build-tools 35.0.0, an NDK and a
debug keystore. Set `ANDROID_SDK_ROOT`, `ANDROID_NDK_ROOT` and
`ANDROID_DEBUG_KEYSTORE` when they are not in the default locations. Set
`OUTPUT_APK` to a new path; the script refuses to overwrite an existing APK.
`APK_PACKAGE` optionally sets a separate application ID to avoid replacing an
existing installation; the Java activity name remains
`org.panvk.loadertest.MainActivity`.
For example:

```sh
ANDROID_SDK_ROOT="$HOME/android/sdk" \
ANDROID_DEBUG_KEYSTORE="$HOME/.android/debug.keystore" \
APK_PACKAGE=org.panvk.presenttest \
OUTPUT_APK=/tmp/panvk-loader-present-test.apk \
  tests/android-loader-app/build-apk.sh
```

For an isolated installation, first check that `org.panvk.presenttest` is not
already installed. Install without `-r`, then put the intended driver in its
private directory. The private file must not already exist. Confirm that neither
`/data/local/tmp/libvulkan_panfrost-present-test.so` nor
`/data/local/tmp/libvulkan_panfrost.so` exists: either readable file takes
precedence over the private file. Also check that the marker files
`/data/local/tmp/panvk-use-system-loader` and
`/data/local/tmp/panvk-test-present-extensions` are absent for a basic,
direct-ICD run. Verify the driver hash before launching:

```sh
adb shell pm path org.panvk.presenttest
adb install /tmp/panvk-loader-present-test.apk
adb shell run-as org.panvk.presenttest mkdir -p files
adb shell "run-as org.panvk.presenttest sh -c 'set -C; cat > files/libvulkan_panfrost.so'" < /path/to/libvulkan_panfrost.so
sha256sum /path/to/libvulkan_panfrost.so
adb shell run-as org.panvk.presenttest sha256sum files/libvulkan_panfrost.so
adb shell am start -n org.panvk.presenttest/org.panvk.loadertest.MainActivity
adb logcat -d -s PanVKLoaderApp:I
```

Only update the isolated installation with `adb install -r` when it is your
own test package and the signing certificate matches. Do not uninstall an
existing installation merely to bypass a signature error.

In the log, `result=0` and `swapchain_result=0` mean `VK_SUCCESS`;
`1000001003` is `VK_SUBOPTIMAL_KHR`. Also check whether the changing image is
visible and whether the test reaches `Gate H: PASS Vulkan WSI 300/300`, noting
whether the log says `draw` or `clear-only`. This isolates PanVK's
Android-surface path; it does not instrument Eden's own `vkQueuePresentKHR`
calls. A successful return alone does not establish that the image was shown.

The same APK can run the offscreen triangle independently from AHB and WSI.
It initializes the image readback buffer and its 64-byte guards to a sentinel,
then verifies every pixel is opaque red or blue, the guards are unchanged,
and an interior red pixel and a blue background pixel match. It logs `F-PASS`
only if all checks pass. Guards cannot detect writes outside the allocation.
Use a fresh process for every run because driver debug options can be cached.
The app's offscreen test disables Mesa's shader disk cache only in that process.
The optional fragment-only mode sets
`PAN_USE_KRAID=fs` in the test process as a comparison (the vertex stage uses
the other compiler); it is not the default and does not change the driver's
default or the system environment.

```sh
adb shell am force-stop org.panvk.presenttest
adb shell am start -n org.panvk.presenttest/org.panvk.loadertest.MainActivity --es test_mode offscreen
adb logcat -d -s PanVKOffscreen:I PanVKLoaderApp:I

adb shell am force-stop org.panvk.presenttest
adb shell am start -n org.panvk.presenttest/org.panvk.loadertest.MainActivity --es test_mode offscreen_fs_control
adb logcat -d -s PanVKOffscreen:I PanVKLoaderApp:I
```

`--es test_mode wsi_draw` forces a WSI draw pipeline even if the AHB test
failed; the default run retains the clear-only fallback in that case. These
diagnostic modes can expose driver crashes and should only be used with the
isolated test package. The WSI run logs semaphore/fence creation and sampled
acquire, submit and present results. It does not instrument the Eden process.

The `wsi_recreate` mode runs 300 frames, waits for device idle, recreates the
swapchain using `oldSwapchain` on the same surface, then runs another 300
frames. Each cycle requires 300 successful acquires, submits and presents and
rejects suboptimal, out-of-date, timeout and device-lost results. It does not
change the window size; if Gate G fails the WSI cycles remain clear-only and
the overall test still fails.

```sh
adb shell am force-stop org.panvk.presenttest
adb shell am start -n org.panvk.presenttest/org.panvk.loadertest.MainActivity --es test_mode wsi_recreate
adb logcat -d -s PanVKLoaderApp:I
```

An independent `sync_fd` mode checks the advertised export capability, submits
an empty batch that signals an exportable binary semaphore, exports it using
`vkGetSemaphoreFdKHR` and validates a returned descriptor with
`SYNC_IOC_FILE_INFO` and a bounded poll. A result of `SKIP` means the capability
is not advertised; `PASS` does not validate a rendered workload or Eden's
native-buffer release path.

The `sync_wait_signal` mode additionally submits one binary semaphore signal,
then a separate `vkQueueSubmit2` waiting on it and signaling the exportable
semaphore before validating the sync-file. It requires Vulkan 1.3 and
`synchronization2`; otherwise it reports `SKIP`. This exercises the queue
sequence used by the runtime's fallback, but does **not** call
`vkQueueSignalReleaseImageANDROID` or verify the Android loader or Eden.

`ahb/anb_release.c` is a separate shell diagnostic for the private Android
native-buffer driver entrypoints. It allocates an AHardwareBuffer, creates a
`VkNativeBufferANDROID` image, acquires it, submits an empty semaphore
dependency, and releases it with one or two wait semaphores (selected by an
optional `1` or `2` argument). It checks the release result and the returned
sync-file when present. It neither renders nor tests the Android system loader
or visible presentation. Run only on a device where the driver can import the
allocated native buffer:

```sh
MESA=/path/to/prepared-mesa
NDK_BIN=/path/to/android-ndk/toolchains/llvm/prebuilt/linux-x86_64/bin
"$NDK_BIN/aarch64-linux-android35-clang" -std=c11 -O2 -Wall -Wextra -Werror \
  -DANDROID_API_LEVEL=35 -I"$MESA/include" -I"$MESA/include/android_stub" \
  tests/ahb/anb_release.c -landroid -ldl -o /tmp/panvk-anb-release
# Copy the executable and the exact driver to unique paths in /data/local/tmp,
# then run: timeout 30 /data/local/tmp/<executable> /data/local/tmp/<driver.so> 2
```

On the Moto G86, the opt-in driver with library SHA-256
`3e79dd987404096bd70b8bcb525a0a871362b45e47d63eb9ee9a9efed0607c37`
created and acquired the native image, but release returned `-13`
(`VK_ERROR_UNKNOWN`) twice each with one and two wait semaphores. The Kbase
sync candidate with library SHA-256
`d30b7c608aefda582058779ffde47bae702a3f41a5fbe3ae32bf915d621c53d8`
passed both cases twice, returning sync-files that were valid and signaled.
It also passed one run per compiler control for compute cases 0–21, the four
linear IDVS modes, and offscreen copy, both in shell and the isolated app
(108 runs). In a separate app UID, both the previous and candidate drivers
failed to create the native-buffer image with `VK_ERROR_INVALID_EXTERNAL_HANDLE`
before the release call. For the candidate, logs reported that the MediaTek
mapper was inaccessible from the app's linker namespace and complete layout
metadata was unavailable. The app-UID release path is therefore untested;
these results do not validate Android-loader or visible presentation.

The loader APK can execute the same native-buffer diagnostic using
`--es test_mode anb_release_1` or `--es test_mode anb_release_2`. It reads the
private `libvulkan_panfrost.so` installed in the test app's files directory.
The test logs `PanVKAnbRelease` and reports failure, not a release result, if
native-buffer image creation fails. Use a separate test package and preserve
any pre-existing private driver when replacing it.

## Kraid compute and IDVS diagnostics

The loader APK also runs independent compute tests using
`--es test_mode compute_N` and `compute_control_N`, where `N` is 0 through
21. Each mode must be run in a fresh process. The default uses the driver's
default compiler configuration; the control sets `PAN_USE_KRAID=vs,fs` in
that process so application compute shaders use the legacy compiler. No
system-wide setting is changed. Cases 0–14 dispatch a 64 by 64 grid; cases
15–21 use one workgroup of 16 lanes. Each case verifies all 4,224 words,
including 64-word guards on each side, ten times.
The guards detect writes into the buffer's guard regions, not accesses
outside the Vulkan allocation.

| Case | Workload |
| --- | --- |
| 0 | Direct indexed writes, 16 by 16 local size |
| 1 | Divergent parity branch, 16 by 16 |
| 2 | Bounds guard for a 61 by 59 region, 16 by 16 |
| 3 | Direct writes, 1 by 1 |
| 4 | Direct writes, 16 by 1 |
| 5 | Permuted columns, 1 by 1 |
| 6–8 | Direct writes, 2, 4 and 8 by 1 |
| 9 | Atomic count of all 16 invocations in each workgroup |
| 10 | Atomic count indexed by local invocation ID |
| 11 | Direct writes using workgroup and local IDs instead of global ID |
| 12 | Atomic output of global ID using an independently calculated address |
| 13 | Read 2,048 words through a 64-bit buffer device address, write to a disjoint region and verify both regions and guards |
| 14 | Upload 2,048 distinct integers to an R32_UINT texture, fetch each texel in compute, and verify both buffer regions and guards |
| 15 | Shift a changing push constant left by 4, once per local lane |
| 16 | Shift a changing push constant right by 2, once per local lane |
| 17 | Multiply the changing push constant by 17 as an arithmetic control |
| 18 | Shift the changing push constant left by 4 and XOR with 1 |
| 19 | Compare a changing push constant with 4 using unsigned greater-than |
| 20 | Compare a changing push constant with 4 using equality |
| 21 | Compare a changing floating-point push constant with 1.0 |

For example:

```sh
adb shell am force-stop org.panvk.presenttest
adb shell am start -n org.panvk.presenttest/org.panvk.loadertest.MainActivity --es test_mode compute_12
adb logcat -d -s PanVKCompute:I PanVKLoaderApp:I
adb shell am force-stop org.panvk.presenttest
adb shell am start -n org.panvk.presenttest/org.panvk.loadertest.MainActivity --es test_mode compute_control_12
adb logcat -d -s PanVKCompute:I PanVKLoaderApp:I
```

`D+E-PASS` requires ten exact matches, including guards. Case 13 requires
Vulkan 1.2 and `bufferDeviceAddress`; an unsupported feature is explicitly
reported as `D+E-SKIP` with result 2. Case 14 similarly skips if the R32_UINT
sampled-image or transfer-destination feature is unavailable. A nonzero
result, timeout, crash, or missing result is not a pass. On the tested G615 device,
the original driver failed cases 4 and 12 under default Kraid and passed the
legacy controls; cases 9–11 passed with both. This narrows the symptom but
does not identify the faulty compiler instruction or establish the cause of
any other application's rendering issue.

Cases 15–21 use one workgroup of 16 lanes and index solely by
`gl_LocalInvocationID`; each of ten iterations changes the push constant and
verifies all 4,224 words including the untouched buffer and guards. In two
independent shell runs and two app-UID runs with shader disk cache disabled,
the original driver with Kraid failed cases 15 and 16 but passed cases 17 and
18; the original driver's legacy compute control passed all four. The
experimental driver passed all four with both compilers in the same contexts.
Textual Kraid IR for the original driver shows the failing operations as
`LSHIFT` or `RSHIFT` with a user FAU source and a small constant; the XOR case
was fused to `LSHIFT_XOR` with its third source in a register. This narrows
the failing pattern independently of global invocation IDs, but does not
prove the behavior of explicit zero sources or all other instructions.
The app's compute tests disable shader disk cache only in their own process.

Cases 19 and 20 expose an additional failure: on the same G615, the original
driver failed both with Kraid and passed the legacy compute control in shell
and in two independent app-UID runs. The shift-only experimental candidate
also failed both in shell. Textual Kraid IR shows `ICMP` using a user FAU
source and a small constant; the ISA describes this as an alias of `ICMP_OR`
with a fixed zero source. A newer, unintegrated candidate that also accounts
for this implicit zero passed cases 15–20 twice in shell with each compiler,
and cases 19–20 twice in the app with each compiler. Its SHA-256 is
`7b24c998210e985bc7128346ecf80b8dc82211236ace920b31f150ea5f6c9330`.
These results support the limited hypothesis, not a general FAU rule; other
instructions, explicit zero sources and additional layouts remain unverified.

Case 21 tests floating-point comparison with values from 0.0 to 4.5 in
increments of 0.5. In two shell runs, the original and both earlier
experimental drivers failed with Kraid and passed the legacy control.
The textual IR shows `FCMP` with a user FAU source and a small constant;
the ISA also specifies an implicit zero for this instruction. A third
unintegrated candidate extends the hypothesis to this instruction and passed
cases 15–21 twice in shell with both compilers. In the app UID, the original
driver failed case 21 twice with Kraid and passed the legacy control twice;
the third candidate passed twice with each compiler. Its SHA-256 is
`f90b3e89dc1fd8253fbc15eeb991733b176b311eecdc72507d3b2a91469617ab`.
These observations do not establish a general hardware rule or prove that
other uses of zero are correct.

For case 13, the original driver failed twice in the app UID with default
Kraid (2,048 output words remained sentinel) and passed twice with the
legacy control. This workload also uses global invocation IDs, so it does
not isolate 64-bit address handling as the cause.

Case 14 likewise failed twice with the original driver and default Kraid in
the app UID, and passed twice with the legacy control. It combines a
buffer-to-image copy, texture fetch and global invocation IDs; failure
does not identify which operation is responsible.

On the same device, an unintegrated experimental driver containing both an
IDVS prototype and an FAU legalization change passed all 13 compute cases in
shell twice with `PAN_USE_KRAID=all`, as well as two sentinel image-copy
trials. The current guarded offscreen test also passed twice with the
experimental driver in shell, checking all 4,096 pixels and 128 guard bytes;
the original driver passed its fragment-only control twice. The experimental
driver's SHA-256 was
`6f5ba3cf668a2d8ca1ad970a4999cea303a5c27a9bfe7c85e48e0ca390d19fff`.
This is not a production fix: implicit-zero FAU accounting, 64-bit sources,
other architectures, and IDVS metadata and workloads still need validation.
An experimental host unit test for an arch 11 shift with one user FAU word
and one nonzero small constant expects one source to be moved to a register.
It passed with the candidate legalizer and failed against the original
legalizer (zero moves). This checks the change in compiler behavior, not
whether the assumed hardware restriction is correct. The ISA also encodes
fixed zero sources for other instruction families, while the candidate only
handles shifts without a logic operation; explicit zero sources and the
general rule remain unverified. Mesa's current Kraid hardware test runner
does not support arch 11, so its host tests cannot establish G615 behavior.
In the app UID, the same experimental driver passed cases 12–14 twice
with default Kraid; cases 13 and 14 also passed twice in shell with both
compilers.
These results cover only these workloads, not other app-UID paths. The
original private app driver was restored and its SHA-256 verified afterward.

`idvs_varying` renders a triangle with interpolated vertex color and reads
the image through `AHardwareBuffer_lock`, rather than the compute-based image
copy path. `idvs_varying_control` uses `PAN_USE_KRAID=fs`, so the vertex
compiler is legacy. The test checks a 60–76 tolerance for red and green at
the interior pixel, alpha, and a blue background pixel. Import errors are
failures, not IDVS results. In the app UID tested here, AHB import failed
before the pipeline was created; this mode cannot currently validate IDVS
there. The same test passed in shell with both the experimental IDVS
prototype and the legacy control, which does not establish app-UID behavior
or validate the complete IDVS implementation.

`idvs_multi` adds smooth and flat varyings plus two vertex push constants:
one changes position and the other changes a varying. It checks two interior
pixels and the background using AHB readback. On the G615 shell, both the
experimental driver and the legacy vertex control passed twice with interior
pixels `(18,68,64,255)` and `(34,68,64,255)`. In the isolated app, both modes
failed during AHB import before pipeline creation, so neither is an IDVS
result in that context.

`idvs_point` draws a nine-pixel point and checks three interior pixels and
two background pixels. `idvs_triangle_psiz` uses the same vertex shader
writing `gl_PointSize` to draw a triangle, exercising the intended
non-point variant. Both require `largePoints` and point size 9 in the
advertised range; unsupported devices report `G-SKIP`. Both passed twice
with the experimental driver and twice with the legacy vertex control in
shell. Pixel checks alone do not prove which internal variant was selected.
TLS, side effects, and every possible FAU layout remain uncovered.

The same four IDVS modes also support `_linear` before the optional
`_control` suffix, for example `idvs_multi_linear_control`. They render to
a linear RGBA8 color attachment and map its host-visible memory directly,
with a color-output-to-host barrier and invalidation for non-coherent memory.
This avoids both AHB import and `vkCmdCopyImageToBuffer`. Unsupported linear
color attachments or host-visible image memory report `G-SKIP` and result 2.
This is a distinct test path; it does not fix or conceal the AHB import
failure. The APK's IDVS modes disable Mesa's shader disk cache in their
isolated test process so a fresh process recompiles the shaders; they do not
change global device settings or delete cached data.

On the G615 app UID, the original driver with legacy vertex compilation
passed `idvs_multi_linear` twice; default Kraid aborted twice after allocating
the image, before reporting pipeline creation. With the experimental driver
identified above, each of `varying`, `multi`, `point`, and `triangle_psiz`
passed twice with default Kraid and twice with the legacy vertex control, in
separate app processes with shader disk cache disabled. For `multi`, diagnostic
metadata reported secondary offset 128 and 32 registers for both variants;
FAU counts were 8 for Kraid and 9 for legacy. For point-size tests, the
no-point-size offset was 128 for Kraid and 256 for legacy; binary sizes differ,
so equal offsets are not expected. These observations cover those shaders only.
The private original driver was restored and its SHA-256 verified. These
results do not prove all IDVS metadata and side-effect cases. The later
FCMP candidate (`f90b3e89dc1fd8253fbc15eeb991733b176b311eecdc72507d3b2a91469617ab`)
also passed the same 16 app-process runs; the original private driver was
again restored and its hash verified.

A subsequent opt-in build from the pinned Mesa base, the standard series
through `jm-v7-wip/0178`, and the experimental FAU and arch 11 IDVS patches
passed compute cases 0–21, all four linear IDVS modes, and the guarded
offscreen copy twice with each compiler control in both shell and app
processes: 216 runs. Its stripped Android library SHA-256 is
`3e79dd987404096bd70b8bcb525a0a871362b45e47d63eb9ee9a9efed0607c37`.
The original private app driver was restored and its hash verified. The
overlay is not part of the default release series; see
[`patches/experimental-kraid-g615/README.md`](../patches/experimental-kraid-g615/README.md).
These tests do not validate AHB import, other GPUs, or third-party applications.

```sh
adb shell am force-stop org.panvk.presenttest
adb shell am start -n org.panvk.presenttest/org.panvk.loadertest.MainActivity --es test_mode idvs_multi_linear
adb logcat -d -s PanVKIdvs:I PanVKLoaderApp:I
adb shell am force-stop org.panvk.presenttest
adb shell am start -n org.panvk.presenttest/org.panvk.loadertest.MainActivity --es test_mode idvs_multi_linear_control
adb logcat -d -s PanVKIdvs:I PanVKLoaderApp:I
adb shell am force-stop org.panvk.presenttest
adb shell am start -n org.panvk.presenttest/org.panvk.loadertest.MainActivity --es test_mode idvs_varying
adb logcat -d -s PanVKIdvs:I PanVKLoaderApp:I
adb shell am force-stop org.panvk.presenttest
adb shell am start -n org.panvk.presenttest/org.panvk.loadertest.MainActivity --es test_mode idvs_multi
adb logcat -d -s PanVKIdvs:I PanVKLoaderApp:I
adb shell am force-stop org.panvk.presenttest
adb shell am start -n org.panvk.presenttest/org.panvk.loadertest.MainActivity --es test_mode idvs_multi_control
adb logcat -d -s PanVKIdvs:I PanVKLoaderApp:I
adb shell am force-stop org.panvk.presenttest
adb shell am start -n org.panvk.presenttest/org.panvk.loadertest.MainActivity --es test_mode idvs_point
adb logcat -d -s PanVKIdvs:I PanVKLoaderApp:I
adb shell am force-stop org.panvk.presenttest
adb shell am start -n org.panvk.presenttest/org.panvk.loadertest.MainActivity --es test_mode idvs_triangle_psiz
adb logcat -d -s PanVKIdvs:I PanVKLoaderApp:I
```

The native binaries can also be built with the NDK and run in a shell using
an explicitly selected driver; the shell may have different mapper access
than an application:

```sh
NDK_BIN="$PWD/work/android-ndk-r30/toolchains/llvm/prebuilt/linux-x86_64/bin"
"$NDK_BIN/aarch64-linux-android35-clang" -O2 -Iwork/mesa/include tests/compute/compute.c -ldl -o /tmp/panvk-compute
"$NDK_BIN/aarch64-linux-android35-clang" -O2 -Iwork/mesa/include tests/ahb/ahb_render.c -landroid -ldl -o /tmp/panvk-idvs
# Push each binary and the intended driver to unique, non-existing device paths.
# Shell examples after pushing:
adb shell 'PAN_USE_KRAID=all /data/local/tmp/panvk-compute /data/local/tmp/libvulkan_panfrost-test.so guarded-12'
adb shell 'PAN_USE_KRAID=vs,fs /data/local/tmp/panvk-compute /data/local/tmp/libvulkan_panfrost-test.so guarded-12'
adb shell 'PAN_USE_KRAID=all /data/local/tmp/panvk-idvs /data/local/tmp/libvulkan_panfrost-test.so varying'
```

Regenerate the checked-in SPIR-V headers with `bash tests/regenerate-kraid-shaders.sh`;
this requires `glslangValidator`, `spirv-val` and Python 3. The generator
validates the SPIR-V before updating the headers.

```sh
adb shell am force-stop org.panvk.presenttest
adb shell am start -n org.panvk.presenttest/org.panvk.loadertest.MainActivity --es test_mode sync_fd
adb logcat -d -s PanVKSyncFd:I PanVKLoaderApp:I
# For the separate wait-and-signal test, force-stop the test app first:
adb shell am force-stop org.panvk.presenttest
adb shell am start -n org.panvk.presenttest/org.panvk.loadertest.MainActivity --es test_mode sync_wait_signal
adb logcat -d -s PanVKSyncFd:I PanVKLoaderApp:I
```

The tests use small allocations, a single queue, bounded frame counts and
bounded Vulkan fence waits. A separate process watchdog is still needed to
bound a driver call that hangs before returning.
