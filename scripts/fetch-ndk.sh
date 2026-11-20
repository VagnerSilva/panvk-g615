#!/bin/sh
# Fetch the official Android NDK r30 for Linux x86_64.
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$ROOT/work"
VERSION="30.0.16248370"
ARCHIVE="android-ndk-r30-linux.zip"
SHA1="5107f898313790e449e87eee2183d9a20602dee9"
URL="https://dl.google.com/android/repository/$ARCHIVE"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --work)
      [ "$#" -ge 2 ] || { echo "ERROR: --work requires a directory" >&2; exit 2; }
      WORK="$2"
      shift 2
      ;;
    *)
      echo "Usage: $0 [--work DIRECTORY]" >&2
      exit 2
      ;;
  esac
done

[ "$(uname -s)" = Linux ] && [ "$(uname -m)" = x86_64 ] || {
  echo "ERROR: official NDK r30 Linux binaries require an x86_64 host" >&2
  exit 1
}
for tool in curl sha1sum unzip; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "ERROR: required tool not found: $tool" >&2
    exit 1
  }
done

DEST="$WORK/ndk/$VERSION"
valid_ndk() {
  [ -f "$1/source.properties" ] &&
    grep -Eq '^Pkg\.Revision[[:space:]]*=[[:space:]]*30[.]0[.]16248370[[:space:]]*$' "$1/source.properties" &&
    [ -x "$1/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android29-clang" ]
}

if [ -e "$DEST" ] || [ -L "$DEST" ]; then
  if [ ! -L "$DEST" ] && valid_ndk "$DEST"; then
    echo "OK ndk=$DEST (already installed)"
    exit 0
  fi
  echo "ERROR: existing destination is not the expected NDK: $DEST" >&2
  exit 1
fi

mkdir -p "$WORK/ndk"
STAGE="$(mktemp -d "$WORK/ndk/.fetch-ndk.XXXXXXXX")"
trap 'rm -rf "$STAGE"' EXIT
trap 'exit 1' HUP INT TERM

curl --fail --location --show-error --proto '=https' --proto-redir '=https' \
  --output "$STAGE/$ARCHIVE" "$URL"
printf '%s  %s\n' "$SHA1" "$STAGE/$ARCHIVE" | sha1sum -c -
unzip -q "$STAGE/$ARCHIVE" -d "$STAGE"

SOURCE="$STAGE/android-ndk-r30"
valid_ndk "$SOURCE" || {
  echo "ERROR: downloaded archive does not contain the expected NDK $VERSION" >&2
  exit 1
}
mv -T -n "$SOURCE" "$DEST"
[ ! -e "$SOURCE" ] || {
  echo "ERROR: destination appeared during installation: $DEST" >&2
  exit 1
}
echo "OK ndk=$DEST"
