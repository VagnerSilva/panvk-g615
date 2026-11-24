# Android/Bionic

For a platform feature or loader correction use the
[mapped entrypoints and recipe D](implementation.md#recipe-d--implement-an-observable-platform-capability).
Keep exact loaded-file ownership and metadata access explicit; a blocked AHB
feature is not permission to bypass the already documented limitation.

## Scope and dependencies

Moto Android app/hot-load, system-loader and WSI boundaries. Build mechanics
belong to [build validation](../../panvk-build-validation/SKILL.md);
Vulkan/AHB/WSI behavior belongs to [PanVK](../../panfrost-panvk/SKILL.md).
Use [architecture](../../../../docs/ARCHITECTURE.md:3) and
[Android build](../../../../scripts/build-android.sh:20) as sources, not
permission to run setup.

Keep host generators and NDK-built target dependencies separate.
Compilation API, Moto API and package minApi are distinct. Confirm actual
toolchain/manifest/ELF/ABI, not only a script's success message.

## Runtime context and existing failure

[E-017 historical evidence](../../../../docs/engineering/mali-kernel-platform/EVIDENCE_REGISTER.md)
reports Moto MC2, MT6878, Android 16/API 36, vendor API 34 and Enforcing.
Actual node permissions, page/GLB details and process context for a future run
must be identified, not copied from Poco.

External-AHB app import is a historical **FAIL (deferred)**: mapper/layout
metadata is unavailable before memory-requirement calculation and DMA-BUF
import. Do not reopen the cause automatically. No policy/namespace bypass or
cookie writes to externally owned buffers.

Driver-owned WSI 300/300 draw, privileged external-AHB control and app
sync_fd/wait-signal are separate historical gates on `a273...` / associated
`a06b...`. Initializer `c453...` / `7d02...` explicitly excludes AHB and
Android presentation. None qualifies the current series.
[Native-buffer release](../../../../tests/README.md:250) uses another
historical binary pair; app image creation fails before release.

## Before authorized execution

Confirm loaded private ICD SHA-256/Build ID, marker and external/private/ZIP
precedence in [test loader](../../../../tests/android-loader-app/jni/panvk_loader_test.c:28).
Use an isolated approved package; preserve existing files and stop on signature
or ownership conflict. Keep draw versus clear-only, readback versus visible
presentation and ANB private entrypoints versus Android loader separate.
An offscreen PASS is not presentation or external-AHB support.
Use [device validation](../workflows/device-validation.md).
