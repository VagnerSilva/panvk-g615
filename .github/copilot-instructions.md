# Copilot instructions

## Build, test, and lint

The driver is built against the exact Mesa revision in `sources.lock`; select
the target through a profile:

```sh
./scripts/fetch-mesa.sh
./scripts/apply-patches.sh --profile g615-v11-csf
./scripts/build-android.sh --profile g615-v11-csf
./scripts/validate-binary.sh --abi android dist/android-g615-v11-csf/libvulkan_panfrost.so
```

For incremental Android builds after setup, use
`ninja -C build/android-bionic`. Build prerequisites and the glibc variant are
documented in [`docs/BUILD-POCO-X6-PRO.md`](../docs/BUILD-POCO-X6-PRO.md) and
[`README.md`](../README.md#building).

Host-side Python tests use `unittest`; there is no single repository-wide test
command. Run the relevant suite, for example:

```sh
python3 -m unittest discover -s tests/dxvk/profile -p 'test_*.py'
python3 -m unittest discover -s tests/runtime-features -p 'test_*.py'
python3 -m unittest discover -s tests/consumer-compat -p 'test_*.py'
python3 tests/validate-package-selfcheck.py
```

To run one test method, filter discovery by file and test name:

```sh
python3 -m unittest discover -s tests/dxvk/profile \
  -p 'test_profile_evaluator_regressions.py' \
  -k test_unknown_comparator_fails_closed
```

Hardware/runtime gates require a supported Mali device and are described in
[`tests/README.md`](../tests/README.md). For the Android apps, run
`./gradlew :app:lintDebug` or `./gradlew :app:assembleDebug` from either
`apps/panvk-launcher/` or `apps/panvk-test/`. The repository does not define a
general C/Python lint command.

## Architecture

This repository carries a profile-selected patch series over pinned upstream
Mesa rather than a standalone copy of the Mesa driver. `sources.lock` records
the source commit; `profiles/*.json` describe GPU architecture, frontend, and
Kbase interface; `patches/` contains the driver changes. `scripts/` fetches
Mesa, applies the profile's patch families, builds, packages, and validates
artifacts.

The primary runtime is the Android/Bionic Vulkan ICD
(`libvulkan_panfrost.so`): Android loader and WSI/AHardwareBuffer integration
feed PanVK, whose `pan_kmod` backend submits through Kbase ioctls to
`/dev/mali0`. A separate glibc build serves Linux userspace environments. The
Android apps in `apps/` provide PanPlay and PanProbe; `tests/` contains both
host-side checks and target-device Vulkan/Kbase gates. See
[`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md).

## Repository-specific conventions

- Treat `sources.lock` and the selected profile as build inputs; do not build
  releases from an unrecorded moving Mesa revision. Compute or refresh patch
  provenance when the source, profile, or patch series changes.
- Keep Mesa changes in the appropriate patch family. Patch files need the
  metadata header described in [`patches/README.md`](../patches/README.md).
  `scripts/apply-patches.sh` intentionally rejects patch drift, offsets, and
  fuzz; do not bypass that check to make a patch appear applicable.
- Keep architecture/frontend-specific behavior in the matching `csf-vN/` or
  `jm-vN/` patch family. JM and CSF are distinct backends, not interchangeable
  build flags.
- Preserve host/target separation in Android cross-builds: Mesa code-generation
  tools are host-built, and target dependencies must come from the NDK-built
  dependency prefix rather than host pkg-config paths.
- Distinguish source implementation, runtime exposure, and device-tested
  behavior in feature evidence. Enumeration alone is not runtime proof; keep
  capability matrices and package validation consistent with the evidence.
- Keep hardware tests bounded and fault-safe: use timeouts, small workloads,
  bounded frames, and one change per run. Do not mix JM and CSF ioctls or infer
  Kbase structures across DDK versions.
