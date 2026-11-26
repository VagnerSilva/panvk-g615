#!/bin/sh
# validate-binary.sh — Gate A static checks (ELF64/AArch64, DT_NEEDED, ICD exports)
# Usage: ./scripts/validate-binary.sh --abi android|glibc <file.so>
set -eu
export LC_ALL=C
ABI=""; SO=""
while [ $# -gt 0 ]; do case "$1" in --abi) ABI="$2"; shift 2;; *) SO="$1"; shift;; esac; done
case "$ABI" in android|glibc) ;; *) echo "FAIL: --abi must be android or glibc" >&2; exit 2;; esac
[ -n "$SO" ] && [ -f "$SO" ] || { echo "file missing: $SO" >&2; exit 1; }
echo "== file =="; file "$SO"
HEADER="$(readelf -h "$SO")"
echo "== readelf -h =="; printf '%s\n' "$HEADER"
DYNAMIC="$(readelf -d "$SO")"
echo "== DT_NEEDED =="; printf '%s\n' "$DYNAMIC" | grep -i needed || true
echo "== ICD exports =="; NM="llvm-nm"; command -v llvm-nm >/dev/null || NM=nm
SYMBOLS="$("$NM" -D --defined-only "$SO")"
printf '%s\n' "$SYMBOLS" | grep -E "vk_icdGetInstanceProcAddr|vk_icdNegotiateLoaderICDInterfaceVersion|hwvulkan_module" || true
FAIL=0
printf '%s\n' "$HEADER" | grep -qE 'Class:[[:space:]]+ELF64' || { echo "FAIL: binary is not ELF64" >&2; FAIL=1; }
printf '%s\n' "$HEADER" | grep -qE 'Machine:[[:space:]]+AArch64' || { echo "FAIL: binary is not AArch64" >&2; FAIL=1; }
printf '%s\n' "$HEADER" | grep -qE 'Type:[[:space:]]+DYN' || { echo "FAIL: binary is not a shared object" >&2; FAIL=1; }
printf '%s\n' "$HEADER" | grep -q 'little endian' || { echo "FAIL: binary is not little-endian" >&2; FAIL=1; }
printf '%s\n' "$SYMBOLS" | grep -qE '[[:space:]]vk_icdGetInstanceProcAddr(@@?[^[:space:]]+)?$' || { echo "FAIL: missing vk_icdGetInstanceProcAddr" >&2; FAIL=1; }
printf '%s\n' "$SYMBOLS" | grep -qE '[[:space:]]vk_icdNegotiateLoaderICDInterfaceVersion(@@?[^[:space:]]+)?$' || { echo "FAIL: missing vk_icdNegotiateLoaderICDInterfaceVersion" >&2; FAIL=1; }
if [ "$ABI" = "android" ]; then
  printf '%s\n' "$DYNAMIC" | grep -q "libc.so.6" && { echo "FAIL: android .so depends on glibc libc.so.6" >&2; FAIL=1; }
  printf '%s\n' "$DYNAMIC" | grep -qi "libX11" && { echo "FAIL: android .so depends on X11" >&2; FAIL=1; }
fi
if [ "$ABI" = "glibc" ]; then
  printf '%s\n' "$DYNAMIC" | grep -q "libc.so.6" || { echo "FAIL: glibc .so missing libc.so.6" >&2; FAIL=1; }
fi
[ "$FAIL" = 0 ] && echo "STATIC-VALIDATION: PASS ($ABI)" || { echo "STATIC-VALIDATION: FAIL ($ABI)" >&2; exit 1; }
