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
