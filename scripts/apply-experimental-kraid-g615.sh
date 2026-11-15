#!/bin/sh
# Apply the experimental Kraid overlay only to its exact, prepared Mesa base.
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MESA=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --mesa) [ "$#" -ge 2 ] || { echo "missing --mesa value" >&2; exit 2; }; MESA="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
[ -n "$MESA" ] || { echo "usage: $0 --mesa <prepared Mesa tree>" >&2; exit 2; }
git -C "$MESA" rev-parse --is-inside-work-tree >/dev/null
if [ ! -f "$MESA/.panvk-patchlevel" ] ||
   [ "$(cat "$MESA/.panvk-patchlevel")" != p0178 ]; then
  echo "expected .panvk-patchlevel to contain p0178; no patches applied" >&2
  exit 1
fi

INDEX="$(mktemp "${TMPDIR:-/tmp}/panvk-experimental-index.XXXXXXXX")"
trap 'rm -f "$INDEX" "$INDEX.lock"' EXIT
GIT_INDEX_FILE="$INDEX" git -C "$MESA" read-tree HEAD
GIT_INDEX_FILE="$INDEX" git -C "$MESA" add -A
# The prepared tree carries p0175; the build marker must instead report p0178.
BASE_LEVEL_BLOB="$(printf 'p0175\n' | git -C "$MESA" hash-object -w --stdin)"
GIT_INDEX_FILE="$INDEX" git -C "$MESA" update-index --add --cacheinfo \
  "100644,$BASE_LEVEL_BLOB,.panvk-patchlevel"
TREE="$(GIT_INDEX_FILE="$INDEX" git -C "$MESA" write-tree)"
EXPECTED=d5db8cd96dc795016f771145459e5cc5907ec761
if [ "$TREE" != "$EXPECTED" ]; then
  echo "unexpected Mesa base tree: $TREE (expected $EXPECTED); no patches applied" >&2
  exit 1
fi

for patch in \
  "$ROOT/patches/experimental-kraid-g615/001-fau-implicit-zero.patch" \
  "$ROOT/patches/experimental-kraid-g615/002-idvs-variants.patch"; do
  if ! result="$(git -C "$MESA" apply --check -v "$patch" 2>&1)"; then
    printf '%s\n' "$result" >&2
    echo "experimental patch does not apply: $patch" >&2
    exit 1
  fi
  if printf '%s\n' "$result" | grep -qiE 'offset|fuzz'; then
    printf '%s\n' "$result" >&2
    echo "experimental patch drift: $patch" >&2
    exit 1
  fi
done
for patch in \
  "$ROOT/patches/experimental-kraid-g615/001-fau-implicit-zero.patch" \
  "$ROOT/patches/experimental-kraid-g615/002-idvs-variants.patch"; do
  git -C "$MESA" apply "$patch"
  echo "APPLIED $(basename "$patch")"
done
