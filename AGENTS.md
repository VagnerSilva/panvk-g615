# AGENTS.md

## Project Overview

Maintain the patch series that adapts Mesa's PanVK Vulkan driver for Arm Mali GPUs using `mali_kbase` (`/dev/mali0`).
Use Meson and Ninja for the Android AArch64/Bionic ICD and the Linux/glibc variant. Use `g615-v11-csf` (Mali-G615, CSF v11) as the development baseline.
Read the [architecture guide](docs/ARCHITECTURE.md) and use the Mesa revision pinned in [`sources.lock`](sources.lock).

## Directory Map

- [`patches/`](patches/) and [`profiles/`](profiles/): patch families and JSON profiles for GPU architecture, frontend, and Kbase interface.
- [`scripts/`](scripts/): Mesa setup, patch application, builds, packaging, and validation.
- [`meson/`](meson/): AArch64 build configurations for Android and Linux.
- [`apps/`](apps/): PanPlay (`panvk-launcher`) and PanProbe (`panvk-test`), with Gradle for app builds and CMake for native code.
- [`tests/`](tests/), [`device/`](device/), and [`tools/`](tools/): host test suites, on-device Vulkan tests, and utilities.
- [`docs/`](docs/), [`compatibility/`](compatibility/), [`validation/`](validation/), and [`worklogs/`](worklogs/): guides, device compatibility data, and runtime evidence.
- [`.github/workflows/`](.github/workflows/): CI automation.
- [`work/`](work/), [`build/`](build/), and [`dist/`](dist/): local sources and dependencies, build directories, and artifacts, respectively. Do not commit them.

## Build, Validation, and Test Commands

Run these commands from the repository root in a disposable workspace. Check the prerequisites in the [README](README.md#building) and the [Poco X6 Pro build guide](docs/BUILD-POCO-X6-PRO.md).
Do not run `fetch-mesa.sh` on a tree you need to preserve. It resets the checkout and removes untracked files from selected Mesa paths.

```sh
./scripts/fetch-mesa.sh
./scripts/bootstrap-host-tools.sh
./scripts/apply-patches.sh --profile g615-v11-csf
./scripts/build-android.sh --profile g615-v11-csf
./scripts/validate-binary.sh --abi android dist/android-g615-v11-csf/libvulkan_panfrost.so
```

- For incremental Android builds after setup, run `ninja -C build/android-bionic`.
- For the Linux/glibc variant, run `./scripts/build-glibc.sh --profile g615-v11-csf`.
- For universal releases, follow the [release guide](docs/RELEASE.md) and use `scripts/prepare-rc5-tree.sh`. Do not publish a profile build as a universal release.

Run the relevant host test suites. There is no single repository-wide test command.

```sh
python3 -m unittest discover -s tests/dxvk/profile -p 'test_*.py'
python3 -m unittest discover -s tests/runtime-features -p 'test_*.py'
python3 -m unittest discover -s tests/consumer-compat -p 'test_*.py'
python3 tests/validate-package-selfcheck.py
```

- From [`apps/panvk-launcher/`](apps/panvk-launcher/) or [`apps/panvk-test/`](apps/panvk-test/), run `./gradlew :app:lintDebug` and `./gradlew :app:assembleDebug` as applicable.
- The repository root has no general C or Python linter or formatter. Run `git diff --check` for whitespace errors and follow `work/mesa/.clang-format` for Mesa code.
- For Vulkan/Kbase tests, follow the [test guide](tests/README.md) on a supported Mali device.

## Critical Rules and Workspace Integrity

1. Treat original files in `work/` as read-only. Never edit, overwrite, or remove them directly, including files in `work/mesa/`, `work/libdrm/`, and `work/android-deps/`.
2. Make changes only through `.patch` files. Generate the patch with `git diff --binary --full-index` in a separate copy, or write a unified diff.
3. Preserve the original paths, directory structure, permissions, and data. Apply patches only to a disposable copy at the correct revision, never to the original.
4. Run `git apply --check --whitespace=error -v change.patch` first. Reject conflicts, offsets, or fuzz. Apply the patch with `git apply change.patch` only after it passes the check.
5. For Mesa changes, keep the patch in `patches/<family>/` with the [required header](patches/README.md). Validate the series with `apply-patches.sh`.
6. Compare the result with `git diff` or `diff`. Confirm that only the intended paths, file modes, and contents changed. Do not suppress patch failures.

## Coding Conventions and Workflow

- Put each change in the patch family that matches its profile. Do not mix JM and CSF or assume different DDK versions share the same UAPI.
- Keep host and target builds separate. Build generators for the host and use NDK-built dependencies for Android. Use a fresh `BDIR` after changing the cross file.
- Recompute the patch series ID when the base revision, profile, or patches change: `python3 scripts/compute-patch-series-id.py --profile g615-v11-csf`.
- Use short, scoped commit subjects. Follow recent prefixes: `feat(tests):`, `feat(patches):`, `docs(copilot):`, or `panvk:` for driver changes.
- Keep `--with-kbase-sync` opt-in and limited to `g615-v11-csf`. Read the [experimental series limitations](patches/experimental-kbase-sync/README.md).
- Before finishing, run the relevant builds, lint checks, and tests. Report the profile, commands run, and anything you did not validate.
- On hardware, use timeouts, small workloads, and one change per run. Do not treat feature enumeration or passing CI as proof of runtime behavior.
