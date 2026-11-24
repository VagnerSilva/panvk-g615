<h1 align="center">Mesa PanVK for Android (mali_kbase)</h1>

<p align="center">
  Open Mesa <b>PanVK</b> Vulkan driver for Mali-G615 CSF v11, talking directly to the vendor <code>mali_kbase</code> kernel driver.
</p>

<p align="center">
  <a href="https://t.me/+E-NhUATmkqE5ODg1"><img src="https://img.shields.io/badge/Telegram-Join%20testers-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Join the Telegram testers group"></a>
  <a href="https://github.com/zenithblue-oss/panvk-kbase-android/releases"><img src="https://img.shields.io/github/v/release/zenithblue-oss/panvk-kbase-android?include_prereleases&sort=date&style=for-the-badge&label=driver&color=orange" alt="Latest driver release"></a>
  <a href="https://github.com/zenithblue-oss/panplay/releases"><img src="https://img.shields.io/github/v/release/zenithblue-oss/panplay?include_prereleases&sort=date&style=for-the-badge&label=PanPlay&logo=android&logoColor=white" alt="Latest PanPlay release"></a>
  <a href="https://github.com/zenithblue-oss/panprobe/releases"><img src="https://img.shields.io/github/v/release/zenithblue-oss/panprobe?include_prereleases&sort=date&style=for-the-badge&label=PanProbe&logo=android&logoColor=white" alt="Latest PanProbe release"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Vulkan-1.4-AC162C?logo=vulkan&logoColor=white" alt="Vulkan 1.4">
  <img src="https://img.shields.io/badge/Mali-G615%20CSF%20v11-0091BD?logo=arm&logoColor=white" alt="Mali G615 CSF v11">
  <img src="https://img.shields.io/badge/DXVK-D3D9%20%7C%2010%20%7C%2011-555" alt="DXVK D3D9, D3D10, D3D11">
  <img src="https://img.shields.io/badge/vkd3d--proton-D3D12%20FL%2011__x-555" alt="vkd3d-proton D3D12 FL 11_x">
  <img src="https://img.shields.io/badge/Mesa-27.0--devel-6E4C9A" alt="Mesa 27.0-devel">
</p>

<!-- Release rule: every release embeds the PanProbe (apps/panvk-test) and PanPlay (apps/panvk-launcher) 3D screenshots here, at the top. -->

<p align="center">
  <img src="https://github.com/zenithblue-oss/panvk-kbase-android/releases/download/panvk-kbase-v26.3.1/panplay.png" alt="PanPlay 1.3.1 on build 122i: Poco X6 Pro (v11), DXVK D3D11 cube, 763 fps" width="49%">
  <img src="https://github.com/zenithblue-oss/panvk-kbase-android/releases/download/panvk-kbase-v26.3.1/panprobe.png" alt="PanProbe 1.3.2 on build 122i: Lenovo TB336FU (v9), 41/41 pass" width="49%">
</p>

> [!IMPORTANT]
> **Latest published release: [Mesa PanVK v26.3.1](https://github.com/zenithblue-oss/panvk-kbase-android/releases/tag/panvk-kbase-v26.3.1)** is the historical universal v6 to v14 build 122i. The Mesa 27 G615-only migration described here is separate from that release.

> [!NOTE]
> **Testers wanted.**
> 1. Install [PanPlay](https://github.com/zenithblue-oss/panplay/releases/latest) and play your games.
> 2. After **every** run, crashed or not, open the session logs screen and tap **Send to cloud** (or **Share as ZIP**).
> 3. Send the link or ZIP to the [Telegram testers group](https://t.me/+E-NhUATmkqE5ODg1) with the game name, your GPU, the FPS you saw and any glitches.

## About

A patch and build layer around pinned upstream Mesa 27. The only active target is Mali-G615 CSF v11 using the `mali_kbase` kernel interface (`/dev/mali0`), on Android/Bionic and Linux/glibc. Only `g615-v11-csf` remains under `profiles/`; build, patch, packaging and release entry points reject other profiles. Historical releases and device evidence are preserved, not qualified for this series.

**Driver identity.** The Mesa 27 G615 candidate reports `driverName` as `panvk` and identifies the Mesa revision in `driverInfo`. The exact string and binary hash depend on the build.

## Supported GPUs

| GPU | Architecture | Frontend | Kernel interface |
|---|---|---|---|
| Mali-G615 | v11 | CSF | `mali_kbase` |

Other GPUs listed in historical release notes and test results are not targets of the Mesa 27 migration.

## Apps

| | App | What it is |
|---|---|---|
| <img src="apps/panvk-launcher/docs/panplay-logo-512.png" width="48" alt="PanPlay logo"> | **PanPlay** (`apps/panvk-launcher`) | Windows game launcher for Android: Wine/Proton with FEX-Emu, a built-in X server, and the PanVK driver bundled. |
| <img src="apps/panvk-test/docs/panprobe-logo-512.png" width="48" alt="PanProbe logo"> | **PanProbe** (`apps/panvk-test`) | Vulkan feature, conformance-style and performance test app. 41 tests. |

**Direct3D through PanPlay**

| API | Path | Support |
|---|---|---|
| D3D9, D3D10, D3D11 | DXVK | D3D11 feature levels 10_0, 10_1, 11_0, 11_1 |
| D3D12 | vkd3d-proton | Feature level 11_x. FL 12_x is reported unsupported and falls back to 11_1; FL 12 is deferred. |
| D3D9 to D3D11 | WineD3D-Zink | Through OpenGL, Zink and PanVK (D3D12 stays on vkd3d-proton) |
| OpenGL | Mesa Zink 26.2.4 | OpenGL games |

PanPlay also offers: Render API per game (Auto, DXVK, VKD3D, WineD3D, OpenGL (Zink), Vulkan, cnc-ddraw), a launch sheet that shows the detected graphics API, built-in Direct3D feature-level tests (D3D12 11_0 to 12_2, D3D11 10_0 to 11_1), Default or EGL present path, and MangoHud 0.8.4 (install in Components; on with every item, "full", by default; global or per-game options). The full list is in `apps/panvk-launcher/app/src/main/kotlin/dev/zenithblue/panvklauncher/WhatsNew.kt` (shown in the app after each update).

## Install

1. Download **PanPlay** from the [releases page](https://github.com/zenithblue-oss/panplay/releases/latest). The PanVK driver is bundled; the device needs `mali_kbase` (most Android phones and tablets with Mali) and Vulkan.
2. Optional: install **PanProbe** from its [releases](https://github.com/zenithblue-oss/panprobe/releases) to check your device (run all tests; 41/41 is a full pass).
3. Standalone driver packages are on the [driver releases page](https://github.com/zenithblue-oss/panvk-kbase-android/releases), for other loaders that can load an alternate Vulkan ICD. Check the checksum in the release notes.

## Usage

- **PanPlay:** add a Windows game or `.exe`, pick a Render API (Auto is fine), and launch. The Controls page and Settings > Graphics hold the HUD and MangoHud options. After a run, use the session logs screen to share logs.
- **PanProbe:** open it and run all tests. Scenario runs for automation are described in `apps/panvk-test`. Results show the `driverInfo` string so you can confirm which build ran.

## Historical tested devices

Historical Mesa 26 builds 115 to 122i, 2026-10-29 to 2026-10-31; these are not evidence of Mesa 27 support for other GPUs. Raw data: the device-run folders under `worklogs/` (each has a `results.md`) and [`docs/PERF-PROGRESS.md`](docs/PERF-PROGRESS.md). "Baseline" is build 116. Each run was done on the build named in its row; most figures are single runs, so treat small percentages as noise.

| Arch | GPU | Device | How tested | PanProbe | PanPlay | Result vs build 116 |
|---|---|---|---|---|---|---|
| v6 | Mali-G72 MP18 | Galaxy S9 SM-G960F (starlte) | Firebase Test Lab | 41/41 | cube pass (122g) | D3D11 cube 96 vs 100 fps (-4 %), D3D9 equal |
| v7 | Mali-G52 MC2 | Galaxy A31 SM-A315N | Firebase Test Lab | 41/41 | cube pass (122g) | D3D11 cube -20 %, D3D9 -26 % on one run; not confirmed |
| v9 | Mali-G57 MC2 | Lenovo TB336FU | local | 41/41 | 1-9 pass | PanProbe much faster; see `docs/PERF-PROGRESS.md` |
| v9 | Mali-G78 | Pixel 6a (bluejay) | Firebase Test Lab | 41/41, 146.7 s vs 155.9 s | pass (122g/122h) | cube equal; D3D10, FL 10_0 to 11_1, D3D12 pass |
| v10 | Mali-G710 MC7 | Pixel 7 (panther) | Firebase Test Lab | 41/41 (116c, 122e/g) | cube pass (122g) | D3D11 cube -11 % on one run; not confirmed |
| v11 | Mali-G615 MC6 | Poco X6 Pro | local | 41/41 cold and warm | all passes | 122g: D3D11 cube 686 vs 505 fps (+36 %), FL 10_0 to 11_1 +45 to +80 %, D3D10 +58 %, D3D12 +27 to +50 %, cold BC decode 540 vs 5027 ms |
| v12 | Immortalis-G720 MC12 | Galaxy Tab S10 Ultra SM-X926B, SM-X920 | RTL | 41/41 | pass | 122h: D3D12 +7 %, PanProbe 8 % faster, FL fps within noise |
| v13 | Immortalis-G925 MC12 | Galaxy Tab S11 Ultra SM-X930 | RTL | 41/41 | pass | 122h: D3D11 cube +19 %, FL +11 to +17 %, D3D12 +13 %, PanProbe 9 % faster; gears equal on repeat runs |
| v14 | Mali-G1-Ultra | Galaxy Tab S12+ SM-X846B, S12 Ultra SM-X946B, S12 SM-X940 | RTL | 41/41 | scenarios 1-9 pass | 122i: equal to slightly faster, PanProbe 8 % faster (X940) |

Notes:
- "RTL" is Samsung Remote Test Lab. Firebase runs use Firebase Test Lab.
- Not every build ran on every device. Some Firebase matrices came back invalid and were not retried (see `2026-10-31-ftl-122h-vs-116/results.md`).
- On v11 the first BC decode with a cold shader cache took about 5 s on build 116; build 122g brings it down to about 0.5 s.
- No fps comparison against the older RC4 release is claimed here.

## Historical known issues

- Fallout 4 on the DXVK path shows a black face.
- D3D11 1 % low fps on v11 is below RC4 (an X server stall at high fps).
- Direct3D 12 feature level 12_x is not supported (reported unsupported, runs as 11_1).
- Small slowdowns in single runs on v6, v7 and v10 PanPlay cubes need an A/B on a second device.
- v15 is not fully supported.

## Building

Run the following only in a disposable workspace: `fetch-mesa.sh` can reset its Mesa checkout.

```sh
./scripts/fetch-mesa.sh
mkdir -p dist/android-g615-v11-csf
./scripts/apply-patches.sh --profile g615-v11-csf \
  --series-manifest dist/android-g615-v11-csf/series-manifest.json
./scripts/build-android.sh --profile g615-v11-csf
./scripts/validate-binary.sh --abi android dist/android-g615-v11-csf/libvulkan_panfrost.so
./scripts/package-android-adpkg.sh --profile g615-v11-csf
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

The Mesa 27 target is the G615 profile, not a universal v6-v14 release. The universal and v9 build entry points and the JM patch families have been retired. Shared fixes survive as CSF v11 patches 235-240; upstream compiler and model support is not deleted. See [`docs/RELEASE.md`](docs/RELEASE.md) for the G615-only release process. The exact Mesa commit is pinned in `sources.lock`.

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
- [wonderkast02/panvk-g720-kbase-csf](https://github.com/wonderkast02/panvk-g720-kbase-csf): CSF / Valhall and 5th Gen reference (kmod backend, CSF lifecycle, AHB, sync, G720 tessellation).
- [LukeValen/panvk-mali-g52](https://github.com/LukeValen/panvk-mali-g52): JM / Bifrost reference.
- [Noysz/panvk-g99-jm](https://github.com/Noysz/panvk-g99-jm) (MIT): JM / Valhall v9 reference. Ported or used as reference in `jm-v9` 003 (multiview/layered, 0042/0048), 007 (resubmit reset, 0072), 008 (async submit events, 0068), 009 (multi-draw indirect, 0044/0039), 010 (robustness2, 0045/0071), 011-013 (XFB, GS and streams, clip/cull, 0060/0063-0066), 014 (tessellation, 0062), 015 (multiViewport, 0066), 016 (queries, 0067) and 018 (per-sample shading and VMR, 0059).
- [FristOneRR-Panvk-Source](https://github.com/FristOneRR-Admin/FristOneRR-Panvk-Source) (Mesa MIT headers): base of the JM kbase submission and v9 JM backend (`jm-v9` 001/002).
- [bmdhacks/malisx2](https://github.com/bmdhacks/malisx2) (MIT): v9 id table (`jm-v9` 021) and kbase JM fixes: atom layout probe, fault propagation, teardown wait (022) and tiler heap commit (023).
- [JimVulkan/mali-panvk](https://github.com/JimVulkan/mali-panvk) (MIT): fill mode reference (`jm-v9` 019).
- Upstream Mesa merge requests [!43414](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/43414) (G68 model row), [!37969](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/37969) (poly_heap on JM) and [!44535](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/44535) (kraid on all Valhall GPUs): v9 references.
- [m8l8th814n-eng/mesa-gs101](https://github.com/m8l8th814n-eng/mesa-gs101): G77/G78 model rows and the G78 transaction elimination finding (facts only, no code; `jm-v9` 021).
- faux123: release notes reporting that cleaning the cache of imported memory before submit fixes black dashes in 32-bit DXVK games (fact only; `jm-v9` 024).
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
