#!/bin/sh
# package-launcher-zips.sh — build Android launcher driver zips and a development adpkg
# (adrenotools, winlator, bannerlator, cmod, ludashi, gamehub). Layouts reproduce the RC4 zips.
# Metadata follows driverInfo (scripts/driver_identity.py); ZIP filenames use
# Pankv-G615-<version>-<launcher>.zip, without the development suffix or commit hashes.
# Usage: ./scripts/package-launcher-zips.sh --so path/libvulkan_panfrost.so [--version v0.1.0-rc4]
#        [--label RC4] [--tag g615-v11-csf] [--mesa-sha 5a07217f (or 10+ chars to set the driverVersion git id)] [--outdir dist] [--only adpkg] [--dev-name NAME]
# CI imports: --source-lock FILE --ci-android-stage DIR --ci-glibc-stage DIR
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SO=""; VER="v0.0.0-dev"; LABEL=""; TAG="g615-v11-csf"; OUTDIR="$ROOT/dist"; MESA8=""; ONLY=""; DEV_NAME=""
SOURCE_LOCK="$ROOT/sources.lock"; CI_ANDROID=""; CI_GLIBC=""
while [ $# -gt 0 ]; do case "$1" in
  --so) SO="$2"; shift 2;; --version) VER="$2"; shift 2;; --label) LABEL="$2"; shift 2;;
  --tag) TAG="$2"; shift 2;; --outdir) OUTDIR="$2"; shift 2;; --mesa-sha) MESA8="$2"; shift 2;;
  --only) ONLY="$2"; shift 2;;
  --dev-name) [ "$#" -ge 2 ] && [ -n "$2" ] || { echo "--dev-name requires a name" >&2; exit 2; }; DEV_NAME="$2"; shift 2;;
  --source-lock) SOURCE_LOCK="$2"; shift 2;;
  --ci-android-stage) CI_ANDROID="$2"; shift 2;;
  --ci-glibc-stage) CI_GLIBC="$2"; shift 2;;
  *) echo "unknown $1" >&2; exit 2;; esac; done
[ "$TAG" = g615-v11-csf ] || {
  echo "unsupported profile: $TAG; only g615-v11-csf is supported" >&2
  exit 2
}
[ -f "$SO" ] || { echo "--so <file> required" >&2; exit 2; }
[ -z "$ONLY" ] || [ "$ONLY" = adpkg ] || { echo "--only supports adpkg" >&2; exit 2; }
[ -z "$DEV_NAME" ] || [ "$ONLY" = adpkg ] || { echo "--dev-name requires --only adpkg" >&2; exit 2; }
[ -f "$SOURCE_LOCK" ] || { echo "source lock missing: $SOURCE_LOCK" >&2; exit 2; }
[ -z "$CI_GLIBC" ] || { [ -n "$CI_ANDROID" ] && [ -z "$ONLY" ]; } || {
  echo "--ci-glibc-stage requires --ci-android-stage and all package outputs" >&2; exit 2;
}
if [ -z "$MESA8" ]; then
  MESA8="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["mesaCommit"][:8])' "$SOURCE_LOCK")"
fi
if [ -z "$LABEL" ]; then
  LABEL="$(echo "${VER#v0.1.0-}" | tr '[:lower:]' '[:upper:]')"
fi
if [ "${#MESA8}" -ge 10 ]; then MESA10="$MESA8"; MESA8="$(echo "$MESA8" | cut -c1-8)"
else MESA10="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["mesaCommit"][:10])' "$SOURCE_LOCK")"; fi
export MESA10
mkdir -p "$OUTDIR"
python3 - "$SO" "$VER" "$LABEL" "$TAG" "$MESA8" "$OUTDIR" "$ROOT" "$ONLY" "$DEV_NAME" "$SOURCE_LOCK" "$CI_ANDROID" "$CI_GLIBC" <<'EOF'
import sys, json, hashlib, zipfile, pathlib, re
so, ver, label, tag, mesa8, outdir, reporoot, only, dev_name, source_lock, ci_android, ci_glibc = sys.argv[1:]
import os
sys.path.insert(0, os.path.join(reporoot, "scripts"))
from driver_identity import identity_for_pin
mesa10 = os.environ.get("MESA10") or mesa8
so = pathlib.Path(so); outdir = pathlib.Path(outdir)
data = so.read_bytes()
sha = hashlib.sha256(data).hexdigest()
pkgver = ver.removeprefix("v")
is_dev = bool(re.search(r'(^|[^a-z])dev([^a-z]|$)', pkgver.lower()))
if only == "adpkg" and not is_dev:
    sys.exit("adpkg import packages require a -dev version; use the release packager for other tiers")
if ci_android and not is_dev:
    sys.exit("CI import packages require a -dev version")
if dev_name and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", dev_name):
    sys.exit("invalid --dev-name: use 1-128 ASCII letters, numbers, '.', '_' or '-'")
lock = json.loads(pathlib.Path(source_lock).read_text())

def ci_stage(directory, abi, payload):
    if not directory:
        return None, {}
    stage = pathlib.Path(directory)
    record_bytes = (stage / "CI-BUILD.json").read_bytes()
    record = json.loads(record_bytes)
    series = (stage / "series-manifest.json").read_bytes()
    expected = {
        "profile": tag, "abi": abi, "releaseTier": "dev",
        "mesaCommit": lock["mesaCommit"], "patchSeriesId": lock["patchSeriesId"],
        "binarySha256": hashlib.sha256(payload).hexdigest(),
        "seriesManifestSha256": hashlib.sha256(series).hexdigest(),
    }
    for key, value in expected.items():
        if record.get(key) != value:
            sys.exit(f"CI {key} does not identify the staged binary")
    if not re.fullmatch(r"[0-9a-f]{40}", record.get("projectCommit", "")):
        sys.exit("CI record needs the exact project commit")
    if abi == "android-aarch64-bionic" and (
        type(record.get("androidApi")) is not int or record["androidApi"] < 35
    ):
        sys.exit("CI Android package requires the recorded API >=35")
    validation = {key: record[key] for key in (
        "profile", "abi", "projectCommit", "mesaCommit", "patchSeriesId",
        "binarySha256", "seriesManifestSha256", "gates",
    )}
    validation.update(status="ci-development",
                      note="CI build evidence only; no device validation is added by packaging.")
    return record, {
        "CI-BUILD.json": record_bytes, "series-manifest.json": series,
        "VALIDATION.json": (json.dumps(validation, indent=2) + "\n").encode(),
    }

android_record, android_provenance = ci_stage(ci_android, "android-aarch64-bionic", data)
glibc_data = None
glibc_record = None
glibc_provenance = {}
if ci_glibc:
    glibc_stage = pathlib.Path(ci_glibc)
    glibc_data = (glibc_stage / "libvulkan_panfrost.so").read_bytes()
    glibc_record, glibc_provenance = ci_stage(ci_glibc, "linux-aarch64-glibc", glibc_data)
    if glibc_record["projectCommit"] != android_record["projectCommit"]:
        sys.exit("CI Android and glibc project commits differ")
    glibc_ident = identity_for_pin(glibc_data, lock)
    glibc_icd = (glibc_stage / "panfrost_icd.aarch64.json").read_bytes()
    if json.loads(glibc_icd)["ICD"]["library_path"] != "./libvulkan_panfrost.so":
        sys.exit("glibc ICD must use the adjacent library")
ident = identity_for_pin(data, lock)
upstream = ident["style"] == "upstream"
if upstream:
    name = ident["packageName"]
    drvver = ident["driverInfo"]
    title = f"{ident['displayName']} (git-{ident['gitSha']})"
    base = f"{title}: Mali-G615 CSF v11 Kbase Vulkan ICD, package {pkgver}."
else:
    name = f"PanVK-kbase-{label}"
    drvver = ident["driverInfo"]
    title = f"PanVK-kbase {label}"
    base = f"PanVK (Mesa) Mali-G615 CSF v11 Kbase Vulkan ICD, {label} build."
zipstem = f"Pankv-G615-{ver.removesuffix('-dev')}"
if dev_name:
    name = dev_name
check = drvver if upstream or android_record else f"PanVK-kbase {label}"
# launcher -> (package id for abs path, minApi, description tail, libname, wrapper-style extras)
L = {
 "adrenotools": dict(minApi=29, desc="Generic adrenotools package.", lib="libvulkan_panfrost.so", app=None),
 "winlator":    dict(minApi=29, desc="Winlator official package (adrenotools layout).", lib="libvulkan_panfrost.so", app=None),
 "bannerlator": dict(minApi=28, app="com.winlator.banner", lib="libvulkan_panfrost.so"),
 "cmod":        dict(minApi=28, app="com.winlator.cmod", lib="libvulkan_panfrost.so"),
 "ludashi":     dict(minApi=28, app="com.winlator.cmod", lib="libvulkan_panfrost.so"),
 "gamehub":     dict(minApi=29, app=None, lib="libvulkan_freedreno.so",
                     desc="GameHub/BannerHub package: the PanVK library is shipped as libvulkan_freedreno.so (name hard-coded by the loader)."),
 "adpkg":       dict(minApi=35, app=None, lib="libvulkan_panfrost.so",
                     desc="Development package; device validation is not included."),
}
if ci_glibc:
    L["emulator"] = dict(app=None, lib="libvulkan_panfrost.so",
                         desc="Development glibc ICD for Bachata/NativeCode; not an Android library.")
def icd(path):
    return json.dumps({"file_format_version":"1.0.0","ICD":{"library_path":path,"api_version":"1.4.363"}}, indent=2) + "\n"
for key, c in L.items():
    if only and key != only:
        continue
    if key == "adpkg" and not is_dev:
        continue
    app = c.get("app")
    is_glibc = key == "emulator"
    payload = glibc_data if is_glibc else data
    payload_sha = hashlib.sha256(payload).hexdigest()
    record = glibc_record if is_glibc else android_record
    if app:
        desc = f"{base} Package for {key} ({app}); see README-{key}.txt for the direct-ICD (no wrapper) setting."
    else:
        desc = f"{base} {c['desc']}"
    meta = {"schemaVersion":1,"name":name,"description":desc,"author":"panvk-kbase-android",
            "packageVersion":pkgver,"vendor":"Mesa","driverVersion":drvver,
            "libraryName":c["lib"], "profile":tag, "panArch":11, "frontend":"CSF"}
    if not is_glibc:
        meta["minApi"] = record["androidApi"] if record else c["minApi"]
    if record:
        meta.update(abi=record["abi"], projectCommit=record["projectCommit"],
                    releaseTier="dev", sourceCommit=record["mesaCommit"])
        if not dev_name:
            meta["name"] = f"{name}-dev-{record['projectCommit'][:8]}"
    if is_glibc:
        meta["driverVersion"] = glibc_ident["driverInfo"]
    files = {"meta.json": (json.dumps(meta, indent=2) + "\n").encode(),
             c["lib"]: payload,
             "SHA256SUMS.txt": f"{payload_sha}  {c['lib']}\n".encode()}
    if key == "adpkg":
        files["VALIDATION.json"] = (json.dumps({
            "binarySha256": sha,
            "status": "not-revalidated-by-packaging",
            "note": "No device validation evidence is included in this development package.",
        }, indent=2) + "\n").encode()
    files.update(glibc_provenance if is_glibc else android_provenance)
    if is_glibc:
        files["panfrost_icd.aarch64.json"] = glibc_icd
    if app:
        root = f"/data/data/{app}/files/contents/adrenotools/{meta['name']}"
        files["panvk_icd.aarch64.json"] = icd("./libvulkan_panfrost.so").encode()
        files["panvk_icd_abs.aarch64.json"] = icd(f"{root}/libvulkan_panfrost.so").encode()
        files[f"README-{key}.txt"] = (
f"""{title} for {key} ({app})
Install: Adrenotools GPU Drivers > Install > pick this zip. It installs to
  {root}/
Direct load (no wrapper ICD): container > Environment, add
  VK_ICD_FILENAMES={root}/panvk_icd_abs.aarch64.json
(container env vars are applied after the app sets the wrapper ICD, so this replaces it).
If the X11 present path fails, also add MESA_VK_WSI_DEBUG=sw.
Fallback (wrapper in path): leave VK_ICD_FILENAMES unset and pick "{meta['name']}" as Graphics Driver Version.
Check: wine log / logcat shows driverInfo "{check}"; .so sha256 {sha}
""").encode()
    out = outdir / (f"{zipstem}.adpkg.zip" if key == "adpkg" else f"{zipstem}-{key}.zip")
    if is_glibc:
        out = outdir / f"{zipstem}-EMULATOR.zip"
    if out.exists(): out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for n in files:
            zi = zipfile.ZipInfo(n, (2026, 10, 17, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, files[n])
    print("OK", out)
EOF
echo "LAUNCHER-ZIPS OK sha256=$(sha256sum "$SO" | cut -d' ' -f1)"
