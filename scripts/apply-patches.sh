#!/bin/sh
# apply-patches.sh — apply qualified patch series for a profile, fail hard on drift
# Usage: ./scripts/apply-patches.sh --profile g615-v11-csf [--mesa work/mesa] [--with-kbase-sync]
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE=""; MESA="$ROOT/work/mesa"; WITH_KBASE_SYNC=false; MANIFEST=""
while [ $# -gt 0 ]; do case "$1" in
  --profile) [ $# -ge 2 ] || { echo "missing --profile value" >&2; exit 2; }; PROFILE="$2"; shift 2;;
  --mesa) [ $# -ge 2 ] || { echo "missing --mesa value" >&2; exit 2; }; MESA="$2"; shift 2;;
  --series-manifest) [ $# -ge 2 ] && [ -n "$2" ] || { echo "missing --series-manifest value" >&2; exit 2; }; MANIFEST="$2"; shift 2;;
  --with-kbase-sync) WITH_KBASE_SYNC=true; shift;;
  *) echo "unknown arg $1" >&2; exit 2;;
esac; done
[ -n "$PROFILE" ] || { echo "--profile required" >&2; exit 2; }
case "$PROFILE" in *[!a-zA-Z0-9_-]*|'') echo "invalid profile: $PROFILE" >&2; exit 2;; esac
[ -f "$ROOT/profiles/$PROFILE.json" ] || { echo "invalid profile: $PROFILE" >&2; exit 2; }
if [ "$WITH_KBASE_SYNC" = true ] && [ "$PROFILE" != "g615-v11-csf" ]; then
  echo "--with-kbase-sync requires --profile g615-v11-csf (Mesa 27)" >&2
  exit 2
fi
[ "$PROFILE" = "g615-v11-csf" ] || {
  echo "unsupported profile: $PROFILE; only g615-v11-csf is supported" >&2
  exit 2
}
ARCH="$(python3 -c "import json;print(json.load(open('$ROOT/profiles/$PROFILE.json'))['panArch'])")"
FRONTEND="$(python3 -c "import json;print(json.load(open('$ROOT/profiles/$PROFILE.json'))['frontend'])")"
SERIES="common android kbase-common app-loader wsi"
if [ "$FRONTEND" = "CSF" ]; then SERIES="$SERIES csf csf-v$ARCH"; else SERIES="$SERIES jm-v$ARCH"; fi
# Universal ICD: jm-v9 sits on top of the csf-v11 series (v9 JM + v10-v14 CSF),
# jm-v7 (Bifrost v6/v7 kbase unblock) on top of jm-v9.
if [ "$PROFILE" = "g615-v11-csf" ]; then SERIES="$SERIES jm-v9 jm-v7"; fi
if [ "$WITH_KBASE_SYNC" = true ]; then SERIES="$SERIES experimental-kbase-sync"; fi
if [ -n "$MANIFEST" ]; then
  MESA_PIN="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["mesaCommit"])' "$ROOT/sources.lock")"
  [ -d "$MESA" ] && [ "$(git -C "$MESA" rev-parse HEAD 2>/dev/null)" = "$MESA_PIN" ] || {
    echo "invalid Mesa checkout: expected pinned commit $MESA_PIN" >&2; exit 1;
  }
  [ -z "$(git -C "$MESA" status --porcelain --untracked-files=all --ignored=matching)" ] || {
    echo "invalid Mesa checkout: working tree must be clean" >&2; exit 1;
  }
  python3 - "$MESA" "$MANIFEST" <<'PY'
import os, sys
mesa = os.path.realpath(sys.argv[1])
original = os.path.abspath(sys.argv[2])
target = os.path.realpath(original)
if os.path.commonpath((mesa, target)) == mesa or os.path.lexists(original) or not os.path.isdir(os.path.dirname(target)) or not os.access(os.path.dirname(target), os.W_OK):
    sys.exit("invalid manifest destination: must be new, outside Mesa, in a writable directory")
PY
fi
echo "profile=$PROFILE arch=$ARCH frontend=$FRONTEND series: $SERIES"
git -C "$MESA" status --porcelain | head -n 5
APPLIED=0
for fam in $SERIES; do
  for p in "$ROOT"/patches/"$fam"/*.patch; do
    [ -e "$p" ] || continue
    if [ "$fam" = "experimental-kbase-sync" ]; then
      case "$(basename "$p")" in
        002-android-release-queue-mesa27.patch|003-kbase-coalesce-mem-sync.patch|004-kbase-sync-file-waiter-lifetime.patch) ;;
        *) continue;;
      esac
    fi
    echo "APPLY [$fam] $(basename "$p")"
    RECOUNT=""
    if ! git -C "$MESA" apply --check "$p" 2>/dev/null; then
      RECOUNT="--recount"
    fi
    # git apply accepts shifted hunks silently; -v reports them, so fail on any offset.
    # shellcheck disable=SC2086
    if ! VOUT="$(git -C "$MESA" apply $RECOUNT --check -v "$p" 2>&1)"; then
      echo "$VOUT" >&2
      echo "PATCH-DRIFT: $p does not apply" >&2
      exit 1
    fi
    if echo "$VOUT" | grep -qiE 'offset|fuzz'; then
      echo "$VOUT" | grep -iE 'offset|fuzz|Checking' >&2
      echo "PATCH-DRIFT: $p applies only with offset/fuzz (refresh hunk headers)" >&2
      exit 1
    fi
    # shellcheck disable=SC2086
    git -C "$MESA" apply $RECOUNT "$p"
    APPLIED=$((APPLIED+1))
  done
  if [ -d "$ROOT/patches/$fam/files" ]; then
    echo "COPY [$fam] files/ -> mesa tree"
    (cd "$ROOT/patches/$fam/files" && find . -type f ! -name README -print0 | tar --null -cf - -T -) | (cd "$MESA" && tar -xf -)
  fi
done
if [ -n "$MANIFEST" ]; then
  python3 - "$ROOT" "$MANIFEST" "$MESA_PIN" "$PROFILE" "$WITH_KBASE_SYNC" $SERIES <<'PY'
import hashlib, json, os, sys
from pathlib import Path
root, target, pin, profile, sync, *families = sys.argv[1:]
root = Path(root)
inputs = []
for family in families:
    directory = root / "patches" / family
    for path in sorted(directory.glob("*.patch")):
        if family == "experimental-kbase-sync" and path.name not in {
            "002-android-release-queue-mesa27.patch",
            "003-kbase-coalesce-mem-sync.patch",
            "004-kbase-sync-file-waiter-lifetime.patch",
        }:
            continue
        inputs.append(path)
    overlay = directory / "files"
    if overlay.is_dir():
        inputs.extend(sorted(p for p in overlay.rglob("*") if p.is_file() and not p.is_symlink() and p.name != "README"))
data = {"mesaCommit": pin, "profile": profile,
        "variant": "kbase-sync-002-004" if sync == "true" else "default",
        "inputs": [{"path": p.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs]}
content = (json.dumps(data, sort_keys=True, indent=2) + "\n").encode()
staging = target + ".partial." + str(os.getpid())
created = False
try:
    with open(staging, "xb") as out:
        created = True
        out.write(content)
    os.link(staging, target)
finally:
    if created:
        os.unlink(staging)
PY
fi
echo "OK applied=$APPLIED profile=$PROFILE"
