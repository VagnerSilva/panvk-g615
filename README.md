<h1 align="center">Mesa PanVK for Mali-G615 (mali_kbase)</h1>

<p align="center">
  Open Mesa <b>PanVK</b> Vulkan driver for Mali-G615 CSF v11, talking directly to the vendor <code>mali_kbase</code> kernel driver.
</p>

<p align="center">
  <a href="https://t.me/+E-NhUATmkqE5ODg1"><img src="https://img.shields.io/badge/Telegram-Join%20testers-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Join the Telegram testers group"></a>
  <a href="https://github.com/zenithblue-oss/panplay/releases"><img src="https://img.shields.io/github/v/release/zenithblue-oss/panplay?include_prereleases&sort=date&style=for-the-badge&label=PanPlay&logo=android&logoColor=white" alt="Latest PanPlay release"></a>
  <a href="https://github.com/zenithblue-oss/panprobe/releases"><img src="https://img.shields.io/github/v/release/zenithblue-oss/panprobe?include_prereleases&sort=date&style=for-the-badge&label=PanProbe&logo=android&logoColor=white" alt="Latest PanProbe release"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Vulkan-1.4-AC162C?logo=vulkan&logoColor=white" alt="Vulkan 1.4">
  <img src="https://img.shields.io/badge/Mali-G615%20CSF%20v11-0091BD?logo=arm&logoColor=white" alt="Mali G615 CSF v11">
  <img src="https://img.shields.io/badge/DXVK-D3D9%20%7C%2010%20%7C%2011-555" alt="DXVK D3D9, D3D10, D3D11">
  <img src="https://img.shields.io/badge/Mesa-27.0--devel-6E4C9A" alt="Mesa 27.0-devel">
</p>

> [!IMPORTANT]
> **G615 only.** This series targets Mali-G615, CSF v11 and `mali_kbase`. Universal packages and other GPUs are not supported. Use packages explicitly built for `g615-v11-csf`; an older release or bundled driver does not establish compatibility with this series.

> [!NOTE]
> **Testers wanted.**
> 1. On a supported G615 device, install [PanPlay](https://github.com/zenithblue-oss/panplay/releases/latest), select a G615 driver package and play your games.
> 2. After **every** run, crashed or not, open the session logs screen and tap **Send to cloud** (or **Share as ZIP**).
> 3. Send the link or ZIP to the [Telegram testers group](https://t.me/+E-NhUATmkqE5ODg1) with the game name, device, driver identity, the FPS you saw and any glitches.

## About

A patch and build layer around pinned upstream Mesa 27 with the integrated Kraid compiler. The only active target is Mali-G615 CSF v11 using the `mali_kbase` kernel interface (`/dev/mali0`), on Android/Bionic and Linux/glibc userspace on the Android device. Only [`g615-v11-csf`](profiles/g615-v11-csf.json) is accepted by build, patch, packaging and release entry points.

**Driver identity.** The Mesa 27 G615 candidate reports `driverName` as `panvk` and identifies the Mesa revision in `driverInfo`. The exact string and binary hash depend on the build.

## Supported target

| GPU | Architecture | Frontend | Kernel interface |
|---|---|---|---|
| Mali-G615 | v11 | CSF | `mali_kbase` |

Both the G615 product and an actual Kbase CSF context are required for device discovery. JM and other GPU products are rejected. G615 support does not guarantee compatibility with every device, kernel or application.

The profile records the Poco X6 Pro / G615 MC6. Moto G86 / G615 MC2 observations are documented separately; do not transfer core masks, kernel details or validation results between these devices.

## Apps

| | App | What it is |
|---|---|---|
| <img src="apps/panvk-launcher/docs/panplay-logo-512.png" width="48" alt="PanPlay logo"> | **PanPlay** (`apps/panvk-launcher`) | Windows game launcher for Android: Wine/Proton with FEX-Emu, a built-in X server, and the PanVK driver bundled. |
| <img src="apps/panvk-test/docs/panprobe-logo-512.png" width="48" alt="PanProbe logo"> | **PanProbe** (`apps/panvk-test`) | Vulkan feature, conformance-style and performance test app. 41 tests. |

**Render paths offered by PanPlay**

| API | Path |
|---|---|
| D3D9, D3D10, D3D11 | DXVK |
| D3D12 | vkd3d-proton |
| D3D9 to D3D11 | WineD3D through Zink and PanVK |
| OpenGL | Mesa Zink |

These are application render paths, not a guarantee of feature-level or game compatibility with every G615 build. Check the exact driver and workload against [`docs/APP-COMPATIBILITY.md`](docs/APP-COMPATIBILITY.md) and [`docs/RUNTIME-FEATURES.md`](docs/RUNTIME-FEATURES.md).

PanPlay also offers: Render API per game (Auto, DXVK, VKD3D, WineD3D, OpenGL (Zink), Vulkan, cnc-ddraw), a launch sheet that shows the detected graphics API, built-in Direct3D feature-level tests (D3D12 11_0 to 12_2, D3D11 10_0 to 11_1), Default or EGL present path, and MangoHud 0.8.4 (install in Components; on with every item, "full", by default; global or per-game options). The full list is in `apps/panvk-launcher/app/src/main/kotlin/dev/zenithblue/panvklauncher/WhatsNew.kt` (shown in the app after each update).

## Install

1. Confirm that the device has **Mali-G615, CSF v11 and `mali_kbase`**. Install **PanPlay** from its [releases page](https://github.com/zenithblue-oss/panplay/releases/latest).
2. Select a driver package explicitly identified as **`g615-v11-csf`**. Older app releases may bundle a legacy driver; verify the loaded `driverInfo` and package identity rather than assuming the bundle is this Mesa 27 series.
3. Optional: install **PanProbe** from its [releases](https://github.com/zenithblue-oss/panprobe/releases) and run its tests. A 41/41 result covers that app's suite, not full Vulkan conformance or all games.
4. For loaders that accept an alternate Vulkan ICD, use a matching G615 standalone package and verify its checksum. Android ADPKG metadata declares `minApi=35`; do not infer support for older Android versions from an API 29 cross-build.

## Usage

- **PanPlay:** add a Windows game or `.exe`, pick a Render API (Auto is fine), and launch. The Controls page and Settings > Graphics hold the HUD and MangoHud options. After a run, use the session logs screen to share logs.
- **PanProbe:** open it and run all tests. Scenario runs for automation are described in `apps/panvk-test`. Results show the `driverInfo` string so you can confirm which build ran.

## Validation and limitations

Validation is scoped to the exact G615 device, kernel, ABI, driver binary and workload. A successful build, feature enumeration or an older device run is not proof of runtime correctness for the current series.

Recent user-reported G615 results for shared-group synchronization and memory budgeting, including normal app exit and reduced apparent heating, are recorded in the [sync series evidence](patches/experimental-kbase-sync/README.md#shared-kbase-group-and-csg-scoped-signals-008-approved-2026-11-26) and [patch 241 comparison](patches/README.md#patch-241-user-reported-approval-2026-11-26). They do not establish universal game compatibility, measured temperature reduction or a guaranteed FPS improvement.

Use [`tests/README.md`](tests/README.md) for bounded device tests. Existing release archives and [`worklogs/`](worklogs/) remain historical evidence only; their support and performance claims are not carried into this G615 series.

## Building

Run the following only in a disposable workspace: `fetch-mesa.sh` can reset its Mesa checkout.

```sh
./scripts/fetch-mesa.sh
mkdir -p dist/android-g615-v11-csf
./scripts/apply-patches.sh --profile g615-v11-csf \
  --series-manifest dist/android-g615-v11-csf/series-manifest.json
./scripts/bootstrap-host-tools.sh
./scripts/build-android.sh --profile g615-v11-csf
./scripts/validate-binary.sh --abi android dist/android-g615-v11-csf/libvulkan_panfrost.so
```

The Android build enables Mesa's experimental Kraid compiler with
`-Dpanfrost-rust=true`. In addition to the Android NDK, it requires Meson 1.7+
and Rust 1.85+ with the Android target (`rustup target add
aarch64-linux-android`), a compatible `bindgen` (0.71.1 or newer; Mesa rejects
0.72.0, 0.73.0, and 0.73.1), and Mesa's Rust dependencies. The cross file
selects the Android Rust target; Meson uses the NDK C compiler as its linker.
If an existing build directory was configured before the cross-file change,
use a new `BDIR` so Meson reads the updated cross file.

On Android G615 builds, Kraid is selected by default. Set
`PAN_USE_KRAID=0` in the environment of the process loading the driver to opt
out; `PAN_USE_KRAID=1` (or `all`) explicitly selects Kraid for all shader
stages. The existing stage selectors (`cs`, `fs`, `vs`, `internal`) remain
available. Non-Android builds remain opt-in. `KRAID_DEBUG=print` enables shader
diagnostics. See
[`docs/BUILD-POCO-X6-PRO.md`](docs/BUILD-POCO-X6-PRO.md) for build setup and
[`tests/README.md`](tests/README.md) for device validation.

To package an existing Android ICD as a development `.adpkg.zip` for app
import, without claiming release or device-validation evidence:

```sh
./scripts/package-launcher-zips.sh \
  --so dist/android-g615-v11-csf/libvulkan_panfrost.so \
  --version v0.0.0-dev --outdir dist/kraid-test --only adpkg
```

This lightweight import package is not the release `.adpkg.zip` produced by
`scripts/package-android-adpkg.sh`; it does not contain release provenance or
device gate evidence. The package does not set runtime environment variables;
Android G615 builds select Kraid by default, with
`PAN_USE_KRAID=0` available to opt out.
The ZIP places `meta.json` before any other JSON entry for importers that
interpret the first JSON file as driver metadata.
For a separate development install, `--dev-name PanVK-G615-experimental`
sets the name in `meta.json` when used with `--only adpkg`. Choose a name not
already used by the target app; driver import and replacement behavior
depends on the app.

Release packaging is separate from compilation and requires the provenance and runtime gates described in [`docs/RELEASE.md`](docs/RELEASE.md). The canonical Android release packager is `scripts/package-android-adpkg.sh`; the lightweight import package above is for development only.

For Linux/glibc userspace on the G615 Android device, follow the [glibc build guide](docs/BUILD-POCO-X6-PRO.md#glibc-cross-build-on-wsl-or-linux) and use `scripts/build-glibc.sh --profile g615-v11-csf`. Android and glibc binaries are not interchangeable.

The Mesa commit is pinned in [`sources.lock`](sources.lock). Upstream compiler and GPU model infrastructure is preserved, but the driver and release scope remains G615 CSF v11 only.

## Layout

```text
sources.lock          exact Mesa commit + reference repos (no moving branches)
profiles/             only g615-v11-csf
patches/              qualified patch families
meson/                cross files (android-aarch64, linux-aarch64-native)
scripts/              fetch / patch / build / package / validate / release
tests/                kbase-probe, vulkan-smoke, compute, offscreen, ahb, ...
apps/                 PanPlay (panvk-launcher) and PanProbe (panvk-test)
docs/                 architecture, build, matrix, perf, runtime features, ...
worklogs/             device run logs and results
```

More: [`docs/RUNTIME-FEATURES.md`](docs/RUNTIME-FEATURES.md) (Vulkan features and extensions, what is and is not supported), [`docs/APP-COMPATIBILITY.md`](docs/APP-COMPATIBILITY.md), [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`CHANGELOG.md`](CHANGELOG.md).

## License

Mesa code remains under its upstream licenses (see `LICENSES/` and
`NOTICE.md`). Build/patch/test scaffolding in this repository is MIT unless
otherwise noted.

## Credits

This project builds on the work of many people. Thank you.

### Driver

- [Mesa](https://gitlab.freedesktop.org/mesa/mesa) / PanVK and Panfrost (MIT): the driver this project patches. Pinned commit in `sources.lock`.
- Arm `mali_kbase` UAPI headers (Linux kernel, GPL-2.0 WITH Linux-syscall-note): vendored, see `NOTICE.md`.
- [wonderkast02](https://github.com/wonderkast02/panvk-g720-kbase-csf): CSF lifecycle, kmod, AHB and synchronization reference.
- [LukeValen](https://github.com/LukeValen/panvk-mali-g52), [Noysz](https://github.com/Noysz/panvk-g99-jm) (MIT), [FristOneRR-Panvk-Source](https://github.com/FristOneRR-Admin/FristOneRR-Panvk-Source) (Mesa MIT headers), [bmdhacks/malisx2](https://github.com/bmdhacks/malisx2) (MIT) and [JimVulkan/mali-panvk](https://github.com/JimVulkan/mali-panvk) (MIT): historical implementation references, not additional supported targets.
- Upstream Mesa merge requests [!43414](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/43414), [!37969](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/37969) and [!44535](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/44535): model, memory and compiler integration references.
- [m8l8th814n-eng/mesa-gs101](https://github.com/m8l8th814n-eng/mesa-gs101): historical model and transaction-elimination findings (facts only, no code).
- faux123: imported-memory cache synchronization findings for 32-bit DXVK (facts only).
- [nangitagamer777-art/PanVK-kbase](https://github.com/nangitagamer777-art/PanVK-kbase) and [Panvk_Kmod](https://github.com/nangitagamer777-art/Panvk_Kmod): implementation history and secondary reference.
- [GunaCharanTeja/panvk-kbase-android](https://github.com/GunaCharanTeja/panvk-kbase-android) (MIT): the cheap BC3 alpha / BC4 / BC5 endpoint-pair-table encoders and the BC1-to-ETC2 encoder ideas ported (adapted, not copied wholesale) into `csf-v11` 206 for the RC5 bc4 BC mode.
- [leegao/bcn_layer](https://github.com/leegao/bcn_layer) (MIT) with libGPUCounters, and [leegao/mesa-funnymdzz](https://github.com/leegao/mesa-funnymdzz): BCn compatibility and secondary references.
- [Khronos](https://www.khronos.org/) Vulkan headers, registry and [VK-GL-CTS](https://github.com/KhronosGroup/VK-GL-CTS): API definitions and conformance testing.

### PanPlay

- [Winlator](https://github.com/brunodev85/winlator) (LGPL-2.1): built-in X server, renderer and touchpad view (vendored in `apps/panvk-launcher/third_party/winlator`).
- [Wine](https://gitlab.winehq.org/wine/wine) (LGPL-2.1-or-later) and Valve's [Proton](https://github.com/ValveSoftware/Proton), via the [GameNative proton-wine](https://github.com/GameNative/proton-wine) arm64ec build. Wine 11.19 `d3dcompiler_43` / `wined3d` (with vkd3d-shader) as the HLSL compiler fix.
- [GameNative](https://github.com/GameNative): `imagefs_bionic` Android userland for Wine.
- [FEX-Emu](https://github.com/FEX-Emu/FEX) (MIT): x86 / x86-64 emulation (ARM64EC and WoW64).
- [DXVK](https://github.com/doitsujin/dxvk) (Zlib): Direct3D 8/9/10/11 to Vulkan.
- [vkd3d-proton](https://github.com/HansKristian-Work/vkd3d-proton) (LGPL-2.1): Direct3D 12 to Vulkan.
- [cnc-ddraw](https://github.com/FunkyFr3sh/cnc-ddraw) (MIT): DirectDraw renderer for old games.
- Microsoft Visual C++ Redistributable (MFC140, VCOMP140): redistributed under Microsoft's redistribution terms.
- [llvm-mingw](https://github.com/mstorsjo/llvm-mingw): Windows cross toolchain for FEX, DXVK and vkd3d-proton.
- [Apache Commons Compress](https://commons.apache.org/proper/commons-compress/) (Apache-2.0), [XZ for Java](https://tukaani.org/xz/java.html) (0BSD) and [zstd-jni](https://github.com/luben/zstd-jni) (BSD-2-Clause): archive unpacking.

### PanProbe and both apps

- [Android Jetpack / AndroidX and Jetpack Compose](https://developer.android.com/jetpack) (Apache-2.0): app UI.
- Android NDK and the Vulkan loader on Android: native test runner and Vulkan info.

Full license notices: `NOTICE.md`, `LICENSES/` and `apps/panvk-launcher/app/src/main/assets/components-NOTICE.txt`.
