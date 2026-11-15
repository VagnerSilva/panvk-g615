#!/bin/bash
set -eu
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-/opt/android-sdk}}"
SDK_BUILD_TOOLS="${SDK_BUILD_TOOLS:-$SDK_ROOT/build-tools/35.0.0}"
ANDROID_JAR="${ANDROID_JAR:-$SDK_ROOT/platforms/android-35/android.jar}"
NDK_ROOT="${ANDROID_NDK_ROOT:-$REPO/work/android-ndk-r30}"
NDK_BIN="$NDK_ROOT/toolchains/llvm/prebuilt/linux-x86_64/bin"
KEYSTORE="${ANDROID_DEBUG_KEYSTORE:-$HOME/.android/debug.keystore}"
OUTPUT_APK="${OUTPUT_APK:-$ROOT/panvk-loader-test.apk}"

for file in "$ANDROID_JAR" "$KEYSTORE"; do
  [ -f "$file" ] || { echo "Missing required file: $file" >&2; exit 1; }
done
for tool in "$NDK_BIN/aarch64-linux-android35-clang" \
            "$SDK_BUILD_TOOLS/aapt2" "$SDK_BUILD_TOOLS/d8" \
            "$SDK_BUILD_TOOLS/apksigner"; do
  [ -x "$tool" ] || { echo "Missing required tool: $tool" >&2; exit 1; }
done
[ ! -e "$OUTPUT_APK" ] || { echo "Refusing to overwrite: $OUTPUT_APK" >&2; exit 1; }
export PATH="$NDK_BIN:$SDK_BUILD_TOOLS:$PATH"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/panvk-loader-build.XXXXXXXX")"
trap 'rm -rf "$TMP"' EXIT

echo "=== 1. Building native shared library ==="
mkdir -p "$TMP/lib/arm64-v8a"
aarch64-linux-android35-clang -O2 -shared -fPIC \
  -I"$REPO/work/mesa/include" \
  -o "$TMP/lib/arm64-v8a/libpanvk_loader_test.so" \
  "$ROOT/jni/panvk_loader_test.c" -landroid -llog
aarch64-linux-android35-clang -O2 -shared -fPIC \
  -I"$REPO/work/mesa/include" -DPANVK_ANDROID_APP_LOG -Dmain=panvk_offscreen_main \
  -o "$TMP/lib/arm64-v8a/libpanvk_offscreen_test.so" \
  "$ROOT/jni/panvk_offscreen_test.c" "$REPO/tests/offscreen/triangle_vb.c" \
  -ldl -llog
aarch64-linux-android35-clang -O2 -shared -fPIC \
  -I"$REPO/work/mesa/include" \
  -o "$TMP/lib/arm64-v8a/libpanvk_sync_fd_test.so" \
  "$ROOT/jni/panvk_sync_fd_test.c" -ldl -llog
aarch64-linux-android35-clang -O2 -shared -fPIC \
  -I"$REPO/work/mesa/include" -DPANVK_ANDROID_APP_LOG -Dmain=panvk_compute_main \
  -o "$TMP/lib/arm64-v8a/libpanvk_compute_test.so" \
  "$ROOT/jni/panvk_compute_test.c" "$REPO/tests/compute/compute.c" -ldl -llog
aarch64-linux-android35-clang -O2 -shared -fPIC \
  -I"$REPO/work/mesa/include" -DPANVK_ANDROID_APP_LOG -Dmain=panvk_idvs_main \
  -o "$TMP/lib/arm64-v8a/libpanvk_idvs_test.so" \
  "$ROOT/jni/panvk_idvs_test.c" "$REPO/tests/ahb/ahb_render.c" -landroid -ldl -llog
aarch64-linux-android35-clang -O2 -shared -fPIC \
  -DANDROID_API_LEVEL=35 -I"$REPO/work/mesa/include" -I"$REPO/work/mesa/include/android_stub" \
  -DPANVK_ANDROID_APP_LOG -Dmain=panvk_anb_release_main \
  -o "$TMP/lib/arm64-v8a/libpanvk_anb_release_test.so" \
  "$ROOT/jni/panvk_anb_release_test.c" "$REPO/tests/ahb/anb_release.c" -landroid -ldl -llog

echo "=== 2. Compiling resources ==="
mkdir -p "$TMP/compiled" "$TMP/generated"
aapt2 compile "$ROOT/res/layout/activity_main.xml" -o "$TMP/compiled/"
aapt2 compile "$ROOT/res/values/strings.xml" -o "$TMP/compiled/"
PACKAGE_ARGS=()
if [ -n "${APK_PACKAGE:-}" ]; then
  PACKAGE_ARGS=(--rename-manifest-package "$APK_PACKAGE" --custom-package org.panvk.loadertest)
fi
aapt2 link -I "$ANDROID_JAR" \
  --manifest "$ROOT/AndroidManifest.xml" \
  -o "$TMP/base.apk" --java "$TMP/generated" --auto-add-overlay \
  "${PACKAGE_ARGS[@]}" \
  "$TMP/compiled/layout_activity_main.xml.flat" \
  "$TMP/compiled/values_strings.arsc.flat"

echo "=== 3. Compiling Java ==="
mkdir -p "$TMP/obj"
javac --release 11 -d "$TMP/obj" -cp "$ANDROID_JAR" \
  "$ROOT/src/org/panvk/loadertest/MainActivity.java" \
  "$TMP/generated/org/panvk/loadertest/R.java"

echo "=== 4. Dexing ==="
d8 --lib "$ANDROID_JAR" --min-api 29 --output "$TMP/" \
  "$TMP"/obj/org/panvk/loadertest/*.class

echo "=== 5. Packaging APK ==="
(cd "$TMP" && zip -q -u base.apk classes.dex lib/arm64-v8a/libpanvk_loader_test.so lib/arm64-v8a/libpanvk_offscreen_test.so lib/arm64-v8a/libpanvk_sync_fd_test.so lib/arm64-v8a/libpanvk_compute_test.so lib/arm64-v8a/libpanvk_idvs_test.so lib/arm64-v8a/libpanvk_anb_release_test.so)
if [ -f "$REPO/build/bcn-layer-android/libbcn_layer.so" ]; then
  cp "$REPO/build/bcn-layer-android/libbcn_layer.so" \
    "$TMP/lib/arm64-v8a/libVkLayer_BCN_BCnLayer.so"
  (cd "$TMP" && zip -q -u base.apk lib/arm64-v8a/libVkLayer_BCN_BCnLayer.so)
fi

echo "=== 6. Signing APK ==="
apksigner sign --ks "$KEYSTORE" --ks-pass pass:android \
  --out "$OUTPUT_APK" "$TMP/base.apk"
echo "SUCCESS: $OUTPUT_APK"
