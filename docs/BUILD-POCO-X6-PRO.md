# Build on Poco X6 Pro (duchamp, Dimensity 8300-Ultra, G615)

Preferred: NativeCode AI -> ARM64 Alpaquita/glibc PRoot -> NDK cross compiler
(Bionic) + native compiler (glibc). Keep checkout + ccache on fast internal
storage (e.g. `/opt/panvk-build/` or app-private bind mount), never SAF/FUSE.

Prerequisites (PRoot): `ccache ninja git meson python clang` + Android NDK
(the original host setup used NDKs under `/opt/android-sdk/ndk/`, including
version 30.0.14904198).

On Linux x86_64, `./scripts/fetch-ndk.sh` downloads the official NDK r30
(`30.0.16248370`) to `work/ndk/30.0.16248370`. It requires `curl`, `sha1sum`,
and `unzip`, and checks Google's published SHA-1 before extraction. It refuses
to replace an existing invalid destination. The official archive does not
provide an ARM64 host toolchain; use a compatible NDK on an ARM64 build host.
Review the [Android SDK license](https://developer.android.com/studio/terms)
before using the NDK. Downloading it does not install all build prerequisites.

To select this NDK for an Android build, use:

```sh
./scripts/build-android.sh --profile g615-v11-csf --ndk "$PWD/work/ndk/30.0.16248370"
```

```sh
./scripts/fetch-mesa.sh
./scripts/bootstrap-host-tools.sh     # build machine = ARM64 glibc, target helpers NOT executed in guest
./scripts/apply-patches.sh --profile g615-v11-csf
./scripts/build-android.sh --profile g615-v11-csf   # Bionic, minimal: PanVK + Kbase + Android WSI
./scripts/build-glibc.sh --profile g615-v11-csf     # glibc ICD for Bachata/NativeCode
```

Incremental loop: `ninja -C build/android-bionic` + `ccache`; never full clean
rebuild per patch; never build unrelated Gallium drivers; no Zink in the
Android app driver unless a consumer needs it.

Dev loop on rooted Poco: sync source -> build changed target -> package
locally -> static validate -> loader-test APK -> bounded Vulkan tests ->
save logs -> Samba S3 (Android gates pass) / NativeCode (glibc gates pass) ->
release candidate only after full gate set.

## glibc series identity

The default glibc build retains `dist/glibc-<profile>/`, as required by
existing packaging scripts. The experimental sync series is explicitly opt-in:

```sh
./scripts/build-glibc.sh --profile g615-v11-csf --with-kbase-sync --serial "$SERIAL"
```

Omit `--serial` on an AArch64 build host. On other hosts confirm the device,
chroot and Kbase access before using ADB. Each run reconstructs Mesa in a new
`build/glibc-replay-<profile>-<pid>` workspace, records the actual ordered
patch and overlay hashes in `series-manifest.json`, and uses the SHA-256 of
that file as its source identity. The opt-in result goes to
`dist/glibc-<profile>-kbase-sync-002-004-<manifest-sha256>/`, separate from
the default destination. Both destinations contain the ICD, ICD JSON and
series manifest and are published only after static validation. An existing
destination is never overwritten; move or archive it explicitly before
rebuilding the same variant. Failed workspaces are retained for diagnosis,
not reused. `--clean` remains accepted but each run is already fresh.

The manifest records source inputs, not toolchain, binary identity or runtime
evidence. Record the compiler/toolchain, Build ID and ICD SHA-256 separately,
and execute the documented glibc device gates before qualifying a build.
The experimental series is not promoted by this workflow.

## glibc cross-build on WSL or Linux

On an x86-64 Debian/Ubuntu-style host, including WSL, the glibc ICD can be
built locally without ADB, a device, NativeCode or a chroot wrapper:

```sh
./scripts/build-glibc.sh --profile g615-v11-csf \
  --cross-file "$PWD/meson/linux-aarch64-debian-cross.ini"
```

The supplied cross file is an example for Debian/Ubuntu multiarch paths. It
requires AArch64 GCC/G++, binutils, the Rust `aarch64-unknown-linux-gnu`
target, bindgen, Meson, Ninja, native host-tool build dependencies and the
AArch64 development dependencies required by Mesa, including libdrm and any
selected WSI dependencies. Adapt a copy of the cross file for other distros,
sysroots or toolchains. Its `pkg_config_libdir` must point to target `.pc`
files and only architecture-independent shared metadata; avoid host library
paths. The target build clears inherited pkg-config path overrides. Native
code generators are built from the same patched Mesa tree in the fresh build
workspace, without the optional shared host-tools cache. The staged ICD JSON
refers to the adjacent library instead of the host's default install path.

The default enables both X11 and Wayland, as in the existing build. For an
explicit compute/offscreen-only build when WSI dependencies are unavailable:

```sh
./scripts/build-glibc.sh --profile g615-v11-csf \
  --cross-file "$PWD/meson/linux-aarch64-debian-cross.ini" --headless
```

Headless does not provide X11 or Wayland WSI. `--with-kbase-sync` remains
opt-in and `--jobs 1` or `--jobs 2` also bounds the host-tool build. The
explicit cross mode ignores an inherited `ANDROID_SERIAL`; it cannot be
combined with `--serial`, `--device-root` or `--chroot-wrapper`. Without
`--cross-file`, the existing
native AArch64 and ADB device-build selection is unchanged.

The resulting AArch64 glibc binary must be compatible with the target's glibc
and libraries. Static validation is not a device test: transfer the ICD and
its manifest to an isolated location in the target glibc environment, verify
their identity and dependencies, and run the relevant hardware gates before
claiming runtime support.
