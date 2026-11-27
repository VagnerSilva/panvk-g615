#!/bin/sh
# build-all.sh — host tools + android + glibc for a profile
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[ "$#" = 2 ] && [ "$1" = --profile ] || { echo "usage: build-all.sh --profile g615-v11-csf" >&2; exit 2; }
PROFILE="$2"
[ "$PROFILE" = "g615-v11-csf" ] || {
  echo "unsupported profile: $PROFILE; only g615-v11-csf is supported" >&2
  exit 2
}
"$ROOT/scripts/bootstrap-host-tools.sh"
"$ROOT/scripts/build-android.sh" --profile "$PROFILE"
"$ROOT/scripts/build-glibc.sh" --profile "$PROFILE"
