# Functional testing and regressions

## Prerequisites and sequence

Receive the ICD, SHA-256, Build ID, pin, applied series/variant, and ABI from
[build-validation](../../panvk-build-validation/SKILL.md). Use the
[execution record](performance-baseline.md). Confirm the Moto and the loaded
identity in the **same context**: shell, app UID, or chroot.
Shell permissions do not establish app access.

Run only the affected gates, in this order: access/loader, device and queue,
compute/readback, specific workload, bounded repetition. An import failure
before submission blocks completion testing; do not call it a GPU hang.

Reuse [tests/README.md](../../../../tests/README.md) as the contract for
building, isolated installation, and loader APK modes. The commands below
are conditional plans, not executions already validated on the Moto.
Prepare the environment through the build skill; do not compile or reinstall
indiscriminately.

## Selection by behavior

| Changed behavior | Existing resource and acceptance | Limitation |
|---|---|---|
| `/dev/mali0`, initialization, and discovery | [probe.c](../../../../tests/kbase-probe/probe.c), [enumerate.c](../../../../tests/vulkan-smoke/enumerate.c); verify GPU/driver, instance/device/queues, and errors | Probing/enumeration does not execute shaders |
| Compute/submission/completion and mapped buffer | [compute.c](../../../../tests/compute/compute.c), without a second argument: `E-compute 10/10`, `D+E-PASS`, exit 0, magic `0x12345678` | Does not establish rendering or WSI correctness |
| Kraid compute regression | Same program, `guarded-N`, N=0..21, or APK `compute_N`; every comparison in the case passes | The `compute_control_N` control changes the compiler; it is not the default result |
| Rendering, transfer/readback, pipeline | [triangle.c](../../../../tests/offscreen/triangle.c): correct interior and background, `F-PASS`, exit 0; loader `offscreen` also verifies pixels/guards | Guards do not detect writes outside the allocation; does not measure bandwidth |
| Memory, descriptors, robustness | PanProbe `descriptor_model`, `robustness2`, `robust_image_access2`; select the affected case and require mismatches=0 and complete execution | Does not replace DMA-BUF or memory-pressure testing |
| Fences, binary semaphores, multi-submit, and idle | [sync_test.c](../../../../tests/sync/sync_test.c): `SYNC-PASS`, exit 0, and readback; `--cross-queue` requires two queues and both 20/20 cycles | Do not validate timelines from this test alone; use [sync-features.c](../../../../tests/features/sync-features.c) for timelines |
| CSF/events and submission stress | [csf-event-regression.c](../../../../device/csf-event-regression.c), PanProbe `csf_event`; bounded [submit_stress](../../../../tests/dxvk/vulkan/submit_stress/submit_stress.c) | Does not directly measure firmware/queue-group latency |
| DMA-BUF import/lifetime, AHB | [ahb.c](../../../../tests/ahb/ahb.c), [fdimport.c](../../../../tests/ahb/fdimport.c); real gate G allocate/properties/import/bind/GPU-write/CPU-verify/release in the loader | Exposed capabilities or an obtained FD do not establish coherency/readback |
| sync_file export/import | Loader `sync_fd`, `sync_wait_signal`; glibc [sync_file_test.c](../../../../tests/sync/sync_file_test.c): 12 cycles and exit 0 | glibc requires the CSF 1.21/4 KiB contract and opt-in; exit 77 = BLOCKED |
| Android native-buffer release | Loader `anb_release_1/2` or [anb_release.c](../../../../tests/ahb/anb_release.c); verify image creation, release, and FD | Does not render; image failure leaves release unexercised |
| WSI and presentation | Loader `wsi_draw` (300 frames), `wsi_recreate` (2x300), acquire/submit/present logs, and a visible image | Recreating at the same size is not resizing; clear-only does not validate drawing |
| Resize and swapchain lifecycle | PanProbe `swapchain_lifecycle`, results and image | Do not extrapolate to another loader/mapper or app |

## Bounded native execution

In an already approved shell/chroot, use an isolated directory with executables
prepared for the correct ABI and an identified ICD:

```sh
sha256sum ./libvulkan_panfrost.so
timeout -k 3s 30s ./compute ./libvulkan_panfrost.so
timeout -k 3s 30s ./triangle ./libvulkan_panfrost.so
timeout -k 3s 30s ./sync-test ./libvulkan_panfrost.so --cross-queue
```

Run each line separately, record the exit status, and stop at the first failure.
Executable names are preparation destinations, not files guaranteed to exist
in the checkout. Check `timeout --help` in the target environment: if the syntax
or kill-after-grace behavior is unavailable, use an already verified bounded
runner or mark BLOCKED. A host-side `adb` timeout alone does not terminate
the remote process.
Android compute writes results to logcat (`PanVKCompute`); stdout alone is
insufficient. Preserve logs for the PID/time window without clearing the buffer.

## Execution under an app UID

Prefer the modes and isolated installation from the
[loader guide](../../../../tests/README.md). The package below must be an
already approved test installation with the private ICD and no higher-priority
drivers or conflicting markers at the guide's paths:

```sh
adb -s "$SERIAL" shell am force-stop org.panvk.presenttest
adb -s "$SERIAL" shell am start -n org.panvk.presenttest/org.panvk.loadertest.MainActivity --es test_mode offscreen
```

Do not operate another user's package. Wait for completion within the approved
deadline and capture process logs; launch returning 0 does not mean test PASS.
For PanProbe, select **only** the listed test and the exact ICD in the UI.
Disable automatic upload, preserve previous logs, and confirm that no uploads
are pending before opening/running. The
[MainActivity](../../../../apps/panvk-test/app/src/main/java/dev/zenithblue/panvktest/MainActivity.kt)
checks for updates on startup, may retry pending uploads, and recreates
`autorun.txt`. Do not use autorun in a real installation or enable
`gameLoop/all` for a focal test. Prefer a native executable/isolated loader
if those conditions cannot be guaranteed.

## Regression and CTS

Repeat the same test on baseline/candidate with fresh processes and identical
data, UID, cache, and limits. Compare output/pixels/values/FDs, not just the
summary. Functional PASS requires all expected checks, completion, and exit 0;
crash/timeout/device-lost/mismatch are FAIL. A missing prerequisite blocks
only the dependent gate. Stability covers only the executed cycles.

The [CTS runner](../../../../scripts/dxvk/run-vk-cts-subset.sh) contains a
`duchamp` guard, historical defaults, and an Alpine (musl) chroot. It is not
a Moto/glibc runner and must not be bypassed. Moto CTS remains BLOCKED until
setup and adaptation are reviewed/authorized. Preserve QPA, case list/hash,
expected/executed counts, and individual statuses. Warnings/NotSupported must
not be counted as functional PASS, even if a historical summary does so.
