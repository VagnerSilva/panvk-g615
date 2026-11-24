# Release

Tiers: `dev` < `alpha` < `beta` < `rc` < `stable`. First Poco build is never
stable. Active tags use `panvk-g615-v11-csf-v27.0.0-beta.1`. Immutable: patch change = new
release even if Mesa SHA unchanged.

The G615 source release series includes Kbase sync 002-005 by default following
user approval on 2026-11-24. `--with-kbase-sync` remains a compatibility option
with the same patch inputs. See the [series approval and reported comparison](../patches/experimental-kbase-sync/README.md#user-reported-nyushu-comparison-and-release-approval).
This source promotion does not rebuild or republish existing assets; preserve
their original manifests, binary hashes and validation evidence.

Android asset: `Mesa-PanVK-Android-<version>-<sha8>.adpkg.zip`
(flat: `libvulkan_panfrost.so + meta.json + MANIFEST.json + SOURCE.json +
VALIDATION.json + series-manifest.json + SHA256SUMS.txt + runtime-feature-matrix.json`).
glibc asset: `Mesa-PanVK-<version>-<sha8>-EMULATOR.zip`
(+ `panfrost_icd.aarch64.json` and the same provenance files).
Launcher zips: `Mesa-PanVK-Android-<version>-<sha8>-<launcher>.zip`.
`<sha8>` is the git sha the driver reports in `driverInfo`
(`Mesa 27.0.0-devel (git-<sha>)`, like an upstream Mesa PanVK development
build); meta.json `name` is `Mesa-PanVK-<Mesa version>-<sha8>` and
`driverVersion` the exact `driverInfo` (`scripts/driver_identity.py`).
Package metadata keeps the canonical profile ID (for example, `g615-v11-csf`)
so release validation can resolve it under `profiles/`. G615 is the only
active profile; packaging rejects other profiles and binaries whose identity
does not match the recorded Mesa pin. Unknown identity is an error, not a
Mesa 26 fallback.
Releases up to RC4 used `PanVK-Kbase-Android-<version>-<mesa8>...` with
`driverInfo` `PanVK-kbase <release> (Mesa ...)`. Release title:
`Mesa PanVK <tag>`; the historical `panvk-kbase-v` tags are not active update inputs.
`minApi` is 35 until an API 29 Bionic rebuild is proven. Do not advertise 29.

App update check: PanPlay and PanProbe accept only `panvk-g615-v11-csf-v` tags
with `libvulkan_panfrost-g615-v11-csf-android-aarch64.so`. Generic assets,
historical universal tags and old pre-migration G615 tags are ignored.
They compare the tag version with the bundled driver's `packageVersion`, which is the Mesa
version from build 115 on (`26.3.0-devel`, was `0.1.0-rc5`). `DriverUpdate.isNewer`
compares major.minor.patch, then beta/rc, so only a tag above 26.3.0 (for example
`panvk-g615-v11-csf-v27.0.0`) can be offered to these builds; a `0.1.x` tag is not.
Bundled universal Mesa 26 binaries and their metadata remain historical
until a replacement binary is qualified; do not relabel them as G615-only.

App versions: PanPlay 1.3.1 (versionCode 45) and PanProbe 1.3.2 (versionCode 21), build 122i, tagged
`panplay-v<version>` and `panprobe-v<version>` in their repos. A new versionCode must be above
every APK handed out: PanPlay 33 (1.2.7), 34 (1.2.8, sideloaded), 35-40 (1.2.9-rc5 test
builds), 41 (1.3.0 build 115 test APK), 42 (build 115 unsigned release APK), 43 (build 115b), 44 (1.3.0: build 115c unsigned release APK and the build 116-122i test/Firebase APKs) and 45 (1.3.1 build 122i unsigned release APK); PanProbe 15 (1.2.7), 16 (1.3.0 build 115 test APK), 17 (build 115 unsigned release APK), 18 (build 115b), 19 (1.3.0 build 115c unsigned release APK), 20 (1.3.1, the build 116-122i test/Firebase APKs) and 21 (1.3.2 build 122i unsigned release APK). The `-PpanprobeSuffix=rc5u` test APKs are a separate package
(`dev.zenithblue.panvktest.rc5u`). Android installs an update only when it is signed with the
same key as the installed APK. The releases up to 1.2.7 are signed with the certificate
SHA-256 `8b10fde8c12eff4a29e99ae669ba88854e6003178d9c3ec299254fe87c76f3bf`, so 1.3.0 must be
signed with that key too (`apksigner verify --print-certs`; unsigned release APKs and the
exact signing steps: [SIGNING.md](SIGNING.md), `scripts/sign-release.sh`). An APK signed with another key
installs only after an uninstall, which deletes the app's data (PanPlay: containers and games).

Every release: `SHA256SUMS.txt + SOURCE.json + VALIDATION.json` with Mesa
commit, patch hash, compiler/NDK/Meson, host, API, Build ID, SHAs, device,
GPU ID, UAPI, all gate results. CI builds `dev` only; beta/rc/stable require
Poco (or declared device) hardware validation evidence. CI success is never a
substitute for `/dev/mali0` runtime testing.

Package validation compares the profile-specific computed patch inventory with
the identifiers in `meta.json`, `MANIFEST.json` and any `SOURCE.json`. For
`g615-v11-csf` it also requires the inventory to match `sources.lock`. A
`not-reproducible` prebuilt cannot pass this reproducible-package gate. These
packages must also contain the complete ordered `series-manifest.json`.
Validation checks it against the selected inputs and their hashes, matches
its digest and variant in SOURCE/MANIFEST/VALIDATION, reads the actual ELF
Build ID, and requires the validation SHA-256 and ABI to identify that binary.
Structured gate evidence accepted as passing must also identify that binary,
including gates resolved through aliases or case-insensitive result fields.
These checks establish artifact identity, not hardware correctness. Preserve
the recorded compiler/NDK/API and build evidence separately; an unrecorded
toolchain cannot qualify a release.

Validation logs must identify the tested ICD by SHA-256, using a driver hash
marker or a `sha256sum` line for `libvulkan_panfrost.so`. The collector accepts
a passing gate only when its log identifies the staged binary and contains no
conflicting ICD hash. Missing or mismatched identities remain untested; a
current binary hash must never be attributed to an older log. Keep each log
scoped to the execution it identifies; a hash marker alone is not proof of
which binary ran.

The default upstream extension audit uses the Mesa 27 G615 snapshot. Generate
new snapshots from the pinned Mesa checkout with `scripts/capture-matrix.py`;
the script records the checkout revision and `VERSION` and fails if the
source matrix is missing. Runtime enumeration and upstream implementation are
separate evidence, and an audit rejects conflicting recorded Mesa revisions.
Enumeration alone does not establish that an extension has been exercised.

Fault safety: hard timeouts, small allocations, tiny images, single queue,
bounded frames, one change per run. Never spam CSF kicks after fault, fake
DRM nodes/features, guess Kbase structs across DDKs, or mix JM/CSF ioctls.
After severe fault: save logs + kernel evidence, stop, reboot if needed.

## Release checklist

- Every release attaches, and embeds at the very top of the release notes
  (before any text section), the latest panvk-test screenshots and the latest
  panvk-launcher 3D (DXVK cube, with HUD) screenshots. Give each launcher image
  its arch and API.
- Embed only committed files, via
  `https://raw.githubusercontent.com/zenithblue-oss/panvk-kbase-android/<tag-or-sha>/<path>`,
  and check each URL returns 200 (`curl -sI`) after publishing. Upload the same
  images as release assets.
- Build assets from a clean worktree of the release commit, not the dirty
  working tree; confirm the patch series applies on the pinned Mesa base.
  This checkout has only the Mesa 27 G615 profile. The universal preparation
  and v9 build scripts and downstream JM series are retired. Do not label a
  G615 build universal. Run release preparation only in a disposable repository
  copy; the fetch script resets its selected Mesa checkout.
- CI publishes only the two validated canonical packages, their matching
  G615-specific raw assets and matching launcher packages, not every file
  found under `dist/`. Beta/rc/stable gates must identify the final binaries.
