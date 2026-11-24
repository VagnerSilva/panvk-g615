# Operational workflow: PanVK Mesa 27 Android/Bionic and Linux/glibc

Run preparation/build commands only from the root of a disposable repository copy, with authorization to apply the series there. Do not use personal paths, artifacts from another session or the original Mesa tree as implicit inputs. For documentary maintenance, use existing scripts and evidence: the build/runtime blocks below are instructions, not mandatory documentation checks.

Use Bash for shell blocks and `set -euo pipefail` to propagate failures, including pipeline inspections. Define each procedure's variables before execution.

The documentary target is Moto G86 / Mali-G615 MC2, `PAN_ARCH=11`, Kbase CSF. Android 16 and CSF 1.21 appear in the historical Moto manifest; confirm the current configuration before hardware tests. G15 is a scope label, not another `PAN_ARCH` value.

## 1. Provenance and dependencies

Read [sources.lock](../../../../sources.lock), the [G615 profile](../../../../profiles/g615-v11-csf.json) and the [patch contract](../../../../patches/README.md). The only profile accepted by the scripts is `g615-v11-csf`; its metadata still describes Poco X6 Pro MC6/MT6897, not Moto MC2/MT6878. Do not change the profile, pin or lock to hide this difference; record the actual device separately.

Before preparing the copy, record:

```sh
git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git diff --stat
git diff --cached --stat
git -C work/mesa rev-parse HEAD
git -C work/mesa status --short --untracked-files=all
python3 -B scripts/compute-patch-series-id.py --profile g615-v11-csf
```

Compare Mesa and the computed hash with the lock. If the Mesa tree does not exist, record it as a missing input before fetching. Preserve necessary local changes and untracked files; exporting only `HEAD` does not include them.

The `patchSeriesId` includes eligible files from unapplied families. It does not prove application. Record the effective variant and obtain `series-manifest.json` using the [applier's](../../../../scripts/apply-patches.sh) `--series-manifest`; this manifest lists the ordered applied inputs. Its SHA-256 is an additional identity, not a replacement for the ICD hash.

Check Git, Python 3/Mako/packaging, Meson, Ninja, `pkg-config`, host C/C++, LLVM, Rust and bindgen. The [README](../../../../README.md#building) records Meson 1.7+, Rust 1.85+, the Android Rust target and bindgen restrictions. Consult Meson for Bison, Flex, `glslangValidator`, LLVM SPIR-V, SPIRV-Tools, host libdrm and expat; not every detected dependency is mandatory. Record versions and origins; install dependencies only after a confirmed missing requirement.

**Script effects:** [fetch-mesa.sh](../../../../scripts/fetch-mesa.sh) takes a positional work directory and performs checkout/reset/clean. [prepare-x11-headers.sh](../../../../scripts/prepare-x11-headers.sh) replaces its prefix. The [Android build](../../../../scripts/build-android.sh) may clean `BDIR` when the release string changes and overwrites the destination ICD. Never run these scripts on original data or destinations that must be preserved.

## 2. Android/Bionic

[fetch-ndk.sh](../../../../scripts/fetch-ndk.sh) provisions NDK r30 `30.0.16248370`, verifies SHA-1 and accepts `--work DIRECTORY`. Its official archive requires a Linux x86_64 host. The build explicitly accepts `--ndk`; r30 is not a hard script check. On an ARM64 host, select a compatible toolchain and also check the dependency script's NDK discovery; do not run the official x86_64 fetch.

The build calls [build-android-deps.sh](../../../../scripts/build-android-deps.sh) and the X11 preparer when prefixes are missing. Target libdrm and sysroot zlib remain separate from the host. X11/XCB use headers and `.pc` files without link libraries; `X11_INCLUDE` selects headers outside `/usr/include`. Do not reuse prefixes from another NDK/API without establishing their provenance.

Linux x86_64 workflow, in an authorized disposable copy with fresh destinations:

```sh
set -euo pipefail
profile=g615-v11-csf
ndk="$PWD/work/ndk/30.0.16248370"
run="$(mktemp -d "$PWD/build-android-review.XXXXXXXX")"
./scripts/fetch-ndk.sh
./scripts/fetch-mesa.sh
./scripts/apply-patches.sh --profile "$profile" \
  --series-manifest "$run/series-manifest.json"
env -u PANVK_HOST_TOOLS_CACHE \
  ./scripts/bootstrap-host-tools.sh --mesa "$PWD/work/mesa" --out "$run/host-tools"
BDIR="$run/bionic" DDIR="$run/dist" HOST_TOOLS="$run/host-tools/bin" \
  ./scripts/build-android.sh --profile "$profile" --api 29 --ndk "$ndk"
sha256sum "$run/series-manifest.json" "$run/dist/libvulkan_panfrost.so"
```

API 29 is the script default, not proof of runtime support at that API. The [Android cross file](../../../../meson/android-aarch64.ini) uses API 35 in its template; the script generates the copy corresponding to `--api`. Check the generated copy, target/sysroot and target `pkg_config_libdir` before interpreting configuration errors. The log above is written to `$run/bionic.log`.

[bootstrap-host-tools.sh](../../../../scripts/bootstrap-host-tools.sh) produces host `mesa_clc`, `vtn_bindgen2` and `panfrost_compile`. Rebuild them after series changes: the opt-in cache uses only the Mesa commit and may retain old codegen. The ICD targets AArch64; WSI `android,x11` does not determine its architecture.

The build enables `-Dpanfrost-rust=true`. [Android 017](../../../../patches/android/017-default-to-kraid-on-android.patch) selects Kraid by default on Android and preserves `PAN_USE_KRAID=0`, `1`/`all` and stage selectors. Record the test process's selection; do not turn a legacy control into Kraid approval.

## 3. Linux/glibc

Use [build-glibc.sh](../../../../scripts/build-glibc.sh), not the Bionic ICD. The [glibc guide](../../../../docs/BUILD-POCO-X6-PRO.md#glibc-cross-build-on-wsl-or-linux) describes dependencies and host selection.

On Linux/WSL x86_64, without ADB:

```sh
./scripts/build-glibc.sh --profile g615-v11-csf --jobs 2 \
  --cross-file "$PWD/meson/linux-aarch64-debian-cross.ini"
```

The [Debian cross file](../../../../meson/linux-aarch64-debian-cross.ini) requires AArch64 GCC/G++/binutils, Rust `aarch64-unknown-linux-gnu`, bindgen, host tools and AArch64 development dependencies. Adapt a copy for another distribution/sysroot. `pkg_config_libdir` must resolve target dependencies, not host libraries.

The default includes X11 and Wayland; add `--headless` only for compute/offscreen without WSI. `--headless` requires `--cross-file`. Local cross-building cannot combine with `--serial`, `--device-root` or `--chroot-wrapper`; `--jobs` accepts 1 or 2 and also limits host bootstrap.

Without a cross file, an AArch64 host uses [linux-aarch64-native.ini](../../../../meson/linux-aarch64-native.ini). On another host, device mode requires `--serial` and chroot confirmation; it transfers files and builds remotely, so it is not a documentary exercise without hardware effects.

Each execution reconstructs the pin and applies the series in `build/glibc-replay-<profile>-<pid>`. The default destination is `dist/glibc-g615-v11-csf`, containing ICD, JSON and manifest. The script rejects existing destinations and retains failed workspaces. Do not remove or move data without authorization. The manifest identifies sources; record toolchain, Build ID and ICD hash separately.

Kraid is not selected by default on glibc. Check its inclusion in the Meson configuration and use `PAN_USE_KRAID=all` in the target process when validation requires Kraid; do not presume equivalence with Android.

In both environments, `--with-kbase-sync` is opt-in in the applier; glibc also accepts it in the build. It applies only 002-004 after the main series. Read the [limitations](../../../../patches/experimental-kbase-sync/README.md); do not promote the variant to default or release. On Android, record the option during application and keep build/package separate; the Android build does not accept this flag.

## 4. ELF and package inspection

Select `so` from the produced destination and `abi=android` or `abi=glibc`, without using an implicit artifact:

```sh
file "$so"
readelf -h -n "$so"
readelf -d "$so"
readelf --version-info "$so"
./scripts/validate-binary.sh --abi "$abi" "$so"
sha256sum "$so"
```

Require ELF64, little-endian and Machine AArch64. Record GNU Build ID; on Android, inspect `.note.android.ident` for API/NDK when present and compare against toolchain/log, without inferring the version from the package name alone. Glibc must show `libc.so.6` and `GLIBC_*` requirements compatible with the target environment; Bionic must not depend on glibc or host X11 libraries. Inspect every `DT_NEEDED` for target availability.

[validate-binary.sh](../../../../scripts/validate-binary.sh) checks some exports/dependencies but does not enforce ELF64/AArch64 or notes. Confirm these fields explicitly. Require defined dynamic exports `vk_icdGetInstanceProcAddr` and `vk_icdNegotiateLoaderICDInterfaceVersion` using `llvm-nm -D --defined-only "$so"` (or `nm`); an undefined symbol does not satisfy the gate.

Use [package-launcher-zips.sh](../../../../scripts/package-launcher-zips.sh) only for Bionic ICD/dev ADPKG, with a `-dev` version and fresh output. Prerequisites: existing `dist/` in the copy, `abi=android` and an inspected ICD; this packager does not check ABI.

```sh
out="$(mktemp -d "$PWD/dist/adpkg-dev.XXXXXXXX")"
./scripts/package-launcher-zips.sh \
  --so "$so" --version v27.0.0-dev --only adpkg \
  --dev-name PanVK-G615-dev --outdir "$out"
```

Set `zip` to the exact path reported by the script and validate without extracting over existing files:

```sh
unzip -t "$zip"
unzip -p "$zip" meta.json
unzip -p "$zip" VALIDATION.json
unzip -p "$zip" SHA256SUMS.txt
unzip -p "$zip" libvulkan_panfrost.so | sha256sum
cmp "$so" <(unzip -p "$zip" libvulkan_panfrost.so)
```

The last command requires Bash. Also compare the hash with `SHA256SUMS.txt`, `libraryName`, profile, `driverVersion` and `minApi: 35`. Build API 29 does not prove package API 29. Dev `VALIDATION.json` contains no hardware approval.

The [Android](../../../../scripts/package-android-adpkg.sh) and [glibc](../../../../scripts/package-glibc.sh) packagers follow a different contract. Use [RELEASE.md](../../../../docs/RELEASE.md) and [validate-package.sh](../../../../scripts/validate-package.sh) for canonical packages, with consistent sources/manifests/evidence. The current checkout is G615-only; the universal workflow was removed.

## 5. Targeted diagnosis

| Symptom / owner | Evidence and action | Verification after correction |
|---|---|---|
| Bindgen includes x86 `mmintrin.h` in AArch64 cross-build | Check the first bindgen command, target and sysroot in the Meson/Ninja log. The signature was reported in the old r27d workflow; do not apply a preventive workaround to r30. | One retry with fresh `BDIR`, explicit target/sysroot, followed by ELF inspection. |
| Missing X11/XCB headers | Check `xcb/xcb.h`, `X11/Xlib-xcb.h`, `X11/xshmfence.h` in `X11_INCLUDE` before invoking the preparer in a disposable prefix. | Meson resolves header-only `.pc` files without host X11 linkage in Bionic. |
| Old codegen after patch changes | Compare the tree used by all three host generators; pin-only caching does not prove freshness. Rebuild generators from the applied series without shared cache. | Regeneration/build of the affected target; record the new artifact. |
| Glibc cross-build fails in Meson | Check AArch64 tools, Rust target and target `.pc` files; `--headless` addresses WSI dependencies only when WSI is not an acceptance criterion. | New isolated execution; no artifact published after failure. |
| Patch drift or hash mismatch | Check pin, order, profile and inputs; prepare a reviewable correction, never ignore offsets/fuzz or update the lock to mask drift. | Strict check and log of authorized application in the copy. |
| Importer rejects ADPKG | Check identity extracted from the ICD, `meta.json`, distinct dev name, hash and minimum API. | Integrity and byte comparison; hardware import is another gate. |
| Gradle requires a license or missing SDK | Use the application error, not the ICD log; do not implicitly accept licenses or install the SDK. | Application gate `BLOCKED` until the prerequisite is resolved. |
| Enumeration succeeds, but compute/render fails | Preserve the first incorrect result/crash, hash, mode and Kraid selector; route to the responsible specialist. | Same bounded case, identity and relevant control; enumeration is not success. |

If bindgen reproduces the exact signature, the Android retry uses the same explicit host/destination/NDK options with:

```sh
BDIR="$run/bionic-bindgen-check" DDIR="$run/dist-bindgen-check" \
HOST_TOOLS="$run/host-tools/bin" \
BINDGEN_EXTRA_CLANG_ARGS="--target=aarch64-linux-android29 --sysroot=$ndk/toolchains/llvm/prebuilt/linux-x86_64/sysroot" \
  ./scripts/build-android.sh --profile g615-v11-csf --api 29 --ndk "$ndk"
```

## 6. Tests and evidence

### Host and applications

Do not run suites to approve text alone. When corresponding behavior changes, select the existing suite:

```sh
python3 -m unittest discover -s tests -p 'test_build_glibc_cross.py'
python3 -m unittest discover -s tests -p 'test_g615_build_series.py'
python3 -m unittest discover -s tests -p 'test_package_launcher_zips.py'
python3 tests/validate-package-selfcheck.py
```

The [DXVK/profile](../../../../tests/dxvk/profile), [runtime-features](../../../../tests/runtime-features) and [consumer-compat](../../../../tests/consumer-compat) suites use `python3 -m unittest discover -s <directory> -p 'test_*.py'`; consumer-compat requires `vk.xml` from prepared Mesa. They are not equivalent to Vulkan execution on the Moto.

PanPlay and PanProbe have their own toolchains: consult [PanPlay Gradle](../../../../apps/panvk-launcher/app/build.gradle.kts) and [PanProbe Gradle](../../../../apps/panvk-test/app/build.gradle.kts). For relevant changes, run `./gradlew :app:lintDebug :app:assembleDebug` from the app directory. Do not run Gradle just to update this skill.

### Functionality and device identity

Before any authorized hardware test: select the serial using `adb devices -l`; record model/SoC, GPU/cores, Android/ROM, kernel, Kbase/UAPI, `/dev/mali0` access, ABI and the identity of the ICD actually loaded. Do not replace the system driver. Use an isolated package/path, timeout, small workloads and one change per run.

Procedures and expected results are in the [test guide](../../../../tests/README.md); this table selects the gate without reimplementing its harnesses:

| Component | Test / acceptance | Evidence limit |
|---|---|---|
| Initialization, device and GPU memory | Guide gates D/E: correct ICD, `vkCreateInstance`, `vkCreateDevice`, queue, mapped buffer, binding and destruction. | Identify PanVK, not incidental lavapipe/vendor; allocation does not prove dispatch. |
| Compute | [compute](../../../../tests/compute): magic mode requires `0x12345678` in 10/10; `compute_N` diagnostics have their own criteria. | Historical [10/10](../../../../validation/g615-v11-csf/gateDE-compute-2026-09-19.txt) identifies MC6; it does not homologate Moto/current series. |
| Rendering | [offscreen](../../../../tests/offscreen), Gate F: triangle readback without clear/blit false positives. | Separate Kraid stage controls and presentation. |
| DMA-BUF / AHardwareBuffer | [ahb](../../../../tests/ahb), Gate G: allocate, query properties, import/bind, write on GPU, verify on CPU and release. | External AHB app-UID, driver-owned WSI buffers and privileged shell are distinct paths. |
| Synchronization / CSF | [sync](../../../../tests/sync): fences, semaphores, idle, cross-queue chains and `sync_file` import. | Confirmed Kbase/CSF access; glibc lifetime test requires opt-in, CSF 1.21 and 4 KiB pages per guide. Does not validate the entire UAPI. |
| Android WSI | [loader app](../../../../tests/android-loader-app), Gate H and `wsi_draw`/`wsi_recreate`: acquire/draw/present/readback per guide. | Private ANB release does not prove the system loader; clear-only does not prove draw. |
| Linux/glibc | Isolated ICD/JSON, compatible dependencies, Kbase access, compute/sync and selected WSI. | Bionic and Poco MC6 do not certify Moto glibc; headless does not provide X11/Wayland. |

Timeout, crash, missing results, device-lost and corruption are never `PASS`. Stability requires recorded cycle count, duration and limits. Performance requires a baseline using the same workload/device/configuration, both ICD hashes and methodology; do not extrapolate from a smoke test.

### Reusable records

- [Moto initializer manifest](../../../../validation/mesa27-large-draw-initializer-fix.json): pinned Mesa, Android 16, G615 MC2, CSF 1.21, binary `c4532ef9…`, series `7d02a194…`; targeted Large_Draw/tessellation/XFB tests. Excludes full CTS, Android presentation and AHB. Sharing the pin does not make it the current series.
- [Platform matrix](../../../../docs/engineering/mali-kernel-platform/COMPATIBILITY_MATRIX.md): Moto reports separated by driver-owned WSI, external-AHB app-UID, sync and glibc. Preserve failures/unknowns; do not turn historical reports into current execution.
- [Experimental sync series](../../../../patches/experimental-kbase-sync/README.md): candidate-specific evidence and shutdown limits; opt-in availability does not imply homologation.

Record each gate's status, command, result, log and identity: project/Mesa revision, profile, `patchSeriesId`, variant, manifest SHA, host/toolchain/API, ICD Build ID/SHA-256, device and Kraid selector. Evidence without sufficient binary association remains historical or `BLOCKED`, never attributed to the current package.

## 7. Gates and documentary audit

| Gate / prerequisite | Procedure and evidence | Acceptance / action on failure |
|---|---|---|
| Provenance / inputs available | Section 1, lock/profile, computed hash; application manifest/log when executed. | Matching identities, drift-free application proven separately; investigate inputs without rewriting history. |
| Toolchain / target selected | Sections 2/3, versions, generated cross file, sysroot and `.pc` resolution. | Host/target separation and correct dependencies; confirmed missing requirements block the build. |
| Build / preparation complete | Selected script, exit status and Meson/Ninja log; glibc ICD/JSON. | Exit 0 and all artifacts present; preserve the first causal error. |
| ELF / artifact available | Section 4, headers/notes, `DT_NEEDED`, defined exports, Build ID/hash. | ELF64 AArch64 and correct ABI; do not accept the script's PASS alone. |
| Package / ICD inspected | Section 4, ZIP test, metadata and byte/hash comparison; canonical validator when applicable. | Consistent content/identity; mismatch is FAIL, not proven execution. |
| Runtime / device authorized and identified | Section 6 and guide, exact ICD logs and complete mode output. | Functional test criterion met; failure or missing prerequisites does not pass the next gate. |
| Stability / workload and limits defined | Cycle logs, duration, errors, completion and identity. | No failures within executed limits; never general certification. |
| Performance / comparable baseline | Same workload/environment, two hashes and reproducible method. | Comparable results; without measurements, remains NOT EXECUTED. |

To audit the skill without builds/hardware, walk through seven exercises: prepare Android; prepare glibc; diagnose compilation; inspect ELF; validate packages; design a functional test; analyze a regression. Use identified scripts, logs and artifacts. Check flags/paths, prerequisites, first error, identity and limits. Without an artifact, validate instructions only and leave execution `NOT EXECUTED` or `BLOCKED`.

For documentary homologation, check local links, Bash block syntax, `git diff --check` and the complete diff limited to these two documents. Edit documentation directly; patches and strict applicability checks are required only for Mesa driver changes. Request final approval; this audit does not homologate the driver or hardware.
