#!/bin/sh
# build-glibc.sh — ARM64 glibc PanVK ICD (Bachata S4 / NativeCode AI)
# Usage: ./scripts/build-glibc.sh --profile g615-v11-csf [options]
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE=""
CLEAN=0
JOBS=2
SERIAL="${ANDROID_SERIAL:-}"
SERIAL_EXPLICIT=false
CROSS_FILE=""
HEADLESS=false
DEVICE_OPTIONS_EXPLICIT=false
WITH_KBASE_SYNC=false
DEVICE_ROOT="/tmp/panvk-glibc"
CHROOT_WRAPPER="/data/local/tmp/nativecode_chroot.sh"
while [ $# -gt 0 ]; do
  case "$1" in
    --profile) [ $# -ge 2 ] || { echo "missing --profile value" >&2; exit 2; }; PROFILE="$2"; shift 2;;
    --clean) CLEAN=1; shift 1;;
    --jobs) [ $# -ge 2 ] || { echo "missing --jobs value" >&2; exit 2; }; JOBS="$2"; shift 2;;
    --serial) [ $# -ge 2 ] || { echo "missing --serial value" >&2; exit 2; }; SERIAL="$2"; SERIAL_EXPLICIT=true; shift 2;;
    --cross-file) [ $# -ge 2 ] && [ -n "$2" ] || { echo "missing --cross-file value" >&2; exit 2; }; CROSS_FILE="$2"; shift 2;;
    --headless) HEADLESS=true; shift;;
    --with-kbase-sync) WITH_KBASE_SYNC=true; shift;;
    --device-root) [ $# -ge 2 ] || { echo "missing --device-root value" >&2; exit 2; }; DEVICE_ROOT="$2"; DEVICE_OPTIONS_EXPLICIT=true; shift 2;;
    --chroot-wrapper) [ $# -ge 2 ] || { echo "missing --chroot-wrapper value" >&2; exit 2; }; CHROOT_WRAPPER="$2"; DEVICE_OPTIONS_EXPLICIT=true; shift 2;;
    *) echo "unknown $1" >&2; exit 2;;
  esac
done
[ -n "$PROFILE" ] || { echo "--profile required" >&2; exit 2; }
case "$PROFILE" in *[!a-zA-Z0-9_-]*|'') echo "invalid profile: $PROFILE" >&2; exit 2;; esac
if [ "$WITH_KBASE_SYNC" = true ] && [ "$PROFILE" != "g615-v11-csf" ]; then
  echo "--with-kbase-sync requires --profile g615-v11-csf" >&2; exit 2
fi
[ "$PROFILE" = "g615-v11-csf" ] || {
  echo "unsupported profile: $PROFILE; only g615-v11-csf is supported" >&2
  exit 2
}
[ -f "$ROOT/profiles/$PROFILE.json" ] || { echo "invalid profile: $PROFILE" >&2; exit 2; }
case "$JOBS" in 1|2) ;; *) echo "--jobs must be 1 or 2" >&2; exit 2;; esac
if [ -n "$CROSS_FILE" ]; then
  [ "$SERIAL_EXPLICIT" = false ] || { echo "--cross-file and --serial cannot be combined" >&2; exit 2; }
  [ "$DEVICE_OPTIONS_EXPLICIT" = false ] || { echo "--cross-file cannot be combined with device options" >&2; exit 2; }
  [ -f "$CROSS_FILE" ] && [ -r "$CROSS_FILE" ] || { echo "cross file not readable: $CROSS_FILE" >&2; exit 2; }
  case "$CROSS_FILE" in /*) ;; *) CROSS_FILE="$PWD/$CROSS_FILE";; esac
elif [ "$HEADLESS" = true ]; then
  echo "--headless requires --cross-file" >&2; exit 2
fi
for path in "$DEVICE_ROOT" "$CHROOT_WRAPPER"; do
  case "$path" in
    /*) ;;
    *) echo "device paths must be absolute: $path" >&2; exit 2;;
  esac
  case "$path" in *[!a-zA-Z0-9_./-]*|*..*) echo "invalid device path: $path" >&2; exit 2;; esac
done
[ -n "$CROSS_FILE" ] || [ "$(uname -m)" = "aarch64" ] || [ -n "$SERIAL" ] || { echo "--serial required for device build (or use --cross-file for a local cross-build)" >&2; exit 2; }
MESA_PIN="$(python3 -c "import json;print(json.load(open('$ROOT/sources.lock'))['mesaCommit'])")"
mkdir -p "$ROOT/build"
RUN="$ROOT/build/glibc-replay-$PROFILE-$$"
mkdir "$RUN" || { echo "BUILD-FAIL: workspace already exists: $RUN" >&2; exit 1; }
MESA="$RUN/mesa"
MANIFEST="$RUN/series-manifest.json"
"$ROOT/scripts/fetch-mesa.sh" "$RUN"
if [ "$WITH_KBASE_SYNC" = true ]; then
  "$ROOT/scripts/apply-patches.sh" --profile "$PROFILE" --mesa "$MESA" --with-kbase-sync --series-manifest "$MANIFEST"
else
  "$ROOT/scripts/apply-patches.sh" --profile "$PROFILE" --mesa "$MESA" --series-manifest "$MANIFEST"
fi
[ "$(git -C "$MESA" rev-parse HEAD)" = "$MESA_PIN" ] || {
  echo "BUILD-FAIL: Mesa HEAD does not match sources.lock" >&2; exit 1;
}

SOURCE_ID="$(sha256sum "$MANIFEST" | cut -d' ' -f1)"
echo "source_id=$SOURCE_ID workspace=$RUN"
if [ "$WITH_KBASE_SYNC" = true ]; then
  FINAL="$ROOT/dist/glibc-$PROFILE-kbase-sync-002-004-$SOURCE_ID"
else
  FINAL="$ROOT/dist/glibc-$PROFILE"
fi
[ ! -e "$FINAL" ] && [ ! -L "$FINAL" ] || { echo "BUILD-FAIL: destination already exists: $FINAL" >&2; exit 1; }
DDIR="$RUN/stage-$SOURCE_ID"
mkdir "$DDIR"
cp "$MANIFEST" "$DDIR/series-manifest.json"

if [ -n "$CROSS_FILE" ]; then
  BDIR="$RUN/linux-glibc-$SOURCE_ID"
  HOST_BUILD="$RUN/host-tools"
  env -u PANVK_HOST_TOOLS_CACHE PANVK_JOBS="$JOBS" "$ROOT/scripts/bootstrap-host-tools.sh" --mesa "$MESA" --out "$HOST_BUILD"
  PLATFORMS=x11,wayland
  [ "$HEADLESS" = false ] || PLATFORMS=
  env -u PKG_CONFIG_PATH -u PKG_CONFIG_LIBDIR -u PKG_CONFIG_SYSROOT_DIR \
    PATH="$HOST_BUILD/bin:$PATH" meson setup "$BDIR" "$MESA" \
      --cross-file "$CROSS_FILE" \
      -Dbuildtype=release -Dplatforms="$PLATFORMS" \
      -Dgallium-drivers= -Dvulkan-drivers=panfrost -Dpanfrost-kmds=kbase \
      -Dmesa-clc=system -Dprecomp-compiler=system \
      -Degl=disabled -Dgles1=disabled -Dgles2=disabled -Dopengl=false \
      -Dglx=disabled -Dgbm=disabled -Dzstd=disabled -Dlibunwind=disabled
  env -u PKG_CONFIG_PATH -u PKG_CONFIG_LIBDIR -u PKG_CONFIG_SYSROOT_DIR \
    PATH="$HOST_BUILD/bin:$PATH" ninja -j"$JOBS" -C "$BDIR"
  SO="$(find "$BDIR" -name libvulkan_panfrost.so | head -n1)"
  [ -n "$SO" ] || { echo "BUILD-FAIL: ICD missing from $BDIR" >&2; exit 1; }
  cp "$SO" "$DDIR/libvulkan_panfrost.so"
  ICD="$(find "$BDIR" -name 'panfrost_icd.*.json' | head -n1)"
  [ -n "$ICD" ] || { echo "BUILD-FAIL: ICD manifest missing from $BDIR" >&2; exit 1; }
  python3 - "$ICD" "$DDIR/panfrost_icd.aarch64.json" <<'PY'
import json, sys
with open(sys.argv[1]) as source:
    manifest = json.load(source)
if not isinstance(manifest["ICD"]["library_path"], str):
    raise ValueError("invalid ICD library_path")
manifest["ICD"]["library_path"] = "./libvulkan_panfrost.so"
with open(sys.argv[2], "w") as destination:
    json.dump(manifest, destination, indent=2)
    destination.write("\n")
PY
elif [ "$(uname -m)" = "aarch64" ]; then
  BDIR="$RUN/linux-glibc-$SOURCE_ID"
  if [ "$CLEAN" = "1" ] || [ ! -f "$BDIR/build.ninja" ]; then
    mkdir -p "$BDIR"
    meson setup "$BDIR" "$MESA" \
      --native-file "$ROOT/meson/linux-aarch64-native.ini" \
      -Dbuildtype=release \
      -Dplatforms=x11,wayland \
      -Dgallium-drivers= \
      -Dvulkan-drivers=panfrost \
      -Dpanfrost-kmds=kbase \
      -Degl=disabled -Dgles1=disabled -Dgles2=disabled -Dopengl=false \
      -Dglx=disabled -Dgbm=disabled -Dzstd=disabled -Dlibunwind=disabled
  fi
  ninja -j"$JOBS" -C "$BDIR"
  SO="$(find "$BDIR" -name libvulkan_panfrost.so | head -n1)"
  [ -n "$SO" ] || { echo "BUILD-FAIL: ICD missing from $BDIR" >&2; exit 1; }
  cp "$SO" "$DDIR/libvulkan_panfrost.so"
  ICD="$(find "$BDIR" -name 'panfrost_icd.*.json' | head -n1)"
  [ -n "$ICD" ] || { echo "BUILD-FAIL: ICD manifest missing from $BDIR" >&2; exit 1; }
  cp "$ICD" "$DDIR/panfrost_icd.aarch64.json"
else
  DEVICE_RUN="$DEVICE_ROOT/$SOURCE_ID/run-$$"
  SRC="$DEVICE_RUN/mesa"
  BDIR="$DEVICE_RUN/build"
  ARCHIVE="$RUN/mesa-$SOURCE_ID.tar.gz"
  tar --exclude=.git --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner \
    -C "$MESA" -czf "$ARCHIVE" .
  ARCHIVE_SHA="$(sha256sum "$ARCHIVE" | cut -d' ' -f1)"
  echo "Host is $(uname -m), dispatching isolated glibc build on device chroot via ADB..."
  adb -s "$SERIAL" shell "mkdir -p /data/local/tmp/chrootAlpine$DEVICE_ROOT/$SOURCE_ID && mkdir /data/local/tmp/chrootAlpine$DEVICE_RUN"
  DEVICE_ARCHIVE="/data/local/tmp/chrootAlpine$DEVICE_RUN/$(basename "$ARCHIVE")"
  adb -s "$SERIAL" push --sync "$ARCHIVE" "$DEVICE_ARCHIVE"
  adb -s "$SERIAL" shell "$CHROOT_WRAPPER sh --user root -- 'set -eu; test \"\$(sha256sum \"$DEVICE_RUN/$(basename "$ARCHIVE")\" | cut -d\" \" -f1)\" = \"$ARCHIVE_SHA\"; mkdir \"$SRC\"; tar -xzf \"$DEVICE_RUN/$(basename "$ARCHIVE")\" -C \"$SRC\"'"
  echo "Configuring and building in chroot..."
  adb -s "$SERIAL" shell "$CHROOT_WRAPPER sh --user root -- '
    if [ ! -f \"$BDIR/build.ninja\" ]; then
      meson setup \"$BDIR\" \"$SRC\" \
        -Dbuildtype=release \
        -Dplatforms=x11,wayland \
        -Dgallium-drivers= \
        -Dvulkan-drivers=panfrost \
        -Dpanfrost-kmds=kbase \
        -Degl=disabled -Dgles1=disabled -Dgles2=disabled -Dopengl=false \
        -Dglx=disabled -Dgbm=disabled -Dzstd=disabled -Dlibunwind=disabled
    fi
    ninja -j$JOBS -C \"$BDIR\"
  '"
  echo "Pulling built glibc ICD..."
  adb -s "$SERIAL" pull "/data/local/tmp/chrootAlpine$BDIR/src/panfrost/vulkan/libvulkan_panfrost.so" "$DDIR/libvulkan_panfrost.so"
  adb -s "$SERIAL" pull "/data/local/tmp/chrootAlpine$BDIR/src/panfrost/vulkan/panfrost_icd.aarch64.json" "$DDIR/panfrost_icd.aarch64.json"
fi

SO="$DDIR/libvulkan_panfrost.so"
[ -f "$SO" ] || { echo "BUILD-FAIL: $SO not found" >&2; exit 1; }
[ -s "$DDIR/panfrost_icd.aarch64.json" ] || { echo "BUILD-FAIL: ICD manifest missing" >&2; exit 1; }
file "$SO" | grep -q 'ELF 64-bit.*ARM aarch64' || {
  echo "BUILD-FAIL: ICD is not AArch64 ELF" >&2; exit 1;
}
readelf --version-info "$SO" | grep -q 'GLIBC_' || {
  echo "BUILD-FAIL: ICD is not glibc-linked" >&2; exit 1;
}

# Static verification of kbase symbols
if readelf -s "$SO" 2>/dev/null | grep -q "kbase_kmod_ops"; then
  echo "VERIFIED: kbase_kmod_ops present in $SO"
elif strings "$SO" | grep -q "kbase_kmod"; then
  echo "VERIFIED: kbase_kmod present in $SO"
else
  echo "FAIL: kbase symbols missing in $SO" >&2
  exit 1
fi

if readelf -s "$SO" 2>/dev/null | grep -E "(panfrost_kmod|panthor_kmod)"; then
  echo "FAIL: unexpected panfrost/panthor symbols found in $SO" >&2
  exit 1
fi

mkdir -p "$ROOT/dist"
# Rename only after every check; do not merge into an existing directory.
python3 - "$DDIR" "$FINAL" <<'PY'
import ctypes, os, sys
libc = ctypes.CDLL(None, use_errno=True)
if libc.renameat2(-100, os.fsencode(sys.argv[1]), -100, os.fsencode(sys.argv[2]), 1) != 0:
    err = ctypes.get_errno()
    raise OSError(err, os.strerror(err), sys.argv[2])
PY
echo "OK glibc build complete: $FINAL/libvulkan_panfrost.so"
