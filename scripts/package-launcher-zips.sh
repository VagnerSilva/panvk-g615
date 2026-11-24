#!/bin/sh
# package-launcher-zips.sh — build Android launcher driver zips and a development adpkg
# (adrenotools, winlator, bannerlator, cmod, ludashi, gamehub). Layouts reproduce the RC4 zips.
# Names follow the driverInfo the .so reports (scripts/driver_identity.py): builds that report it like upstream
# Mesa ("Mesa 26.3.0-devel (git-6a5d4e2756)") get meta name "Mesa-PanVK-26.3.0-devel-6a5d4e27", that driverInfo
# as driverVersion and Mesa-PanVK-Android-<version>-<git sha8>-<launcher>.zip; older "PanVK-kbase <release>"
# builds keep the RC4 names (PanVK-kbase-<label>, PanVK-Kbase-Android-<version>-<mesa8>-<launcher>.zip).
# Usage: ./scripts/package-launcher-zips.sh --so path/libvulkan_panfrost.so [--version v0.1.0-rc4]
#        [--label RC4] [--tag g615-v11-csf] [--mesa-sha 5a07217f (or 10+ chars to set the driverVersion git id)] [--outdir dist] [--only adpkg] [--dev-name NAME]
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SO=""; VER="v0.0.0-dev"; LABEL=""; TAG="g615-v11-csf"; OUTDIR="$ROOT/dist"; MESA8=""; ONLY=""; DEV_NAME=""
while [ $# -gt 0 ]; do case "$1" in
  --so) SO="$2"; shift 2;; --version) VER="$2"; shift 2;; --label) LABEL="$2"; shift 2;;
  --tag) TAG="$2"; shift 2;; --outdir) OUTDIR="$2"; shift 2;; --mesa-sha) MESA8="$2"; shift 2;;
  --only) ONLY="$2"; shift 2;;
  --dev-name) [ "$#" -ge 2 ] && [ -n "$2" ] || { echo "--dev-name requires a name" >&2; exit 2; }; DEV_NAME="$2"; shift 2;;
  *) echo "unknown $1" >&2; exit 2;; esac; done
[ "$TAG" = g615-v11-csf ] || {
  echo "unsupported profile: $TAG; only g615-v11-csf is supported" >&2
  exit 2
}
[ -f "$SO" ] || { echo "--so <file> required" >&2; exit 2; }
[ -z "$ONLY" ] || [ "$ONLY" = adpkg ] || { echo "--only supports adpkg" >&2; exit 2; }
[ -z "$DEV_NAME" ] || [ "$ONLY" = adpkg ] || { echo "--dev-name requires --only adpkg" >&2; exit 2; }
if [ -z "$MESA8" ]; then
  MESA8="$(python3 -c "import json;print(json.load(open('$ROOT/sources.lock'))['mesaCommit'][:8])")"
fi
if [ -z "$LABEL" ]; then
  LABEL="$(echo "${VER#v0.1.0-}" | tr '[:lower:]' '[:upper:]')"
fi
if [ "${#MESA8}" -ge 10 ]; then MESA10="$MESA8"; MESA8="$(echo "$MESA8" | cut -c1-8)"
else MESA10="$(python3 -c "import json;print(json.load(open('$ROOT/sources.lock'))['mesaCommit'][:10])")"; fi
export MESA10
mkdir -p "$OUTDIR"
python3 - "$SO" "$VER" "$LABEL" "$TAG" "$MESA8" "$OUTDIR" "$ROOT" "$ONLY" "$DEV_NAME" <<'EOF'
import sys, json, hashlib, zipfile, pathlib, re
so, ver, label, tag, mesa8, outdir, reporoot, only, dev_name = sys.argv[1:]
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
if dev_name and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", dev_name):
    sys.exit("invalid --dev-name: use 1-128 ASCII letters, numbers, '.', '_' or '-'")
ident = identity_for_pin(data, json.loads((pathlib.Path(reporoot) / "sources.lock").read_text()))
upstream = ident["style"] == "upstream"
if upstream:
    name = ident["packageName"]
    drvver = ident["driverInfo"]
    title = f"{ident['displayName']} (git-{ident['gitSha']})"
    base = f"{title}: Mali-G615 CSF v11 Kbase Vulkan ICD, package {pkgver}."
    zipstem = f"Mesa-PanVK-Android-{ver}-{ident['sha8']}"
else:
    name = f"PanVK-kbase-{label}"
    drvver = ident["driverInfo"]
    title = f"PanVK-kbase {label}"
    base = f"PanVK (Mesa) Mali-G615 CSF v11 Kbase Vulkan ICD, {label} build."
    zipstem = f"PanVK-Kbase-Android-{ver}-{mesa8}"
if dev_name:
    name = dev_name
check = drvver if upstream else f"PanVK-kbase {label}"
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
def icd(path):
    return json.dumps({"file_format_version":"1.0.0","ICD":{"library_path":path,"api_version":"1.4.363"}}, indent=2) + "\n"
for key, c in L.items():
    if only and key != only:
        continue
    if key == "adpkg" and not is_dev:
        continue
    app = c.get("app")
    if app:
        desc = f"{base} Package for {key} ({app}); see README-{key}.txt for the direct-ICD (no wrapper) setting."
    else:
        desc = f"{base} {c['desc']}"
    meta = {"schemaVersion":1,"name":name,"description":desc,"author":"panvk-kbase-android",
            "packageVersion":pkgver,"vendor":"Mesa","driverVersion":drvver,"minApi":c["minApi"],
            "libraryName":c["lib"], "profile":tag, "panArch":11, "frontend":"CSF"}
    files = {"meta.json": (json.dumps(meta, indent=2) + "\n").encode(),
             c["lib"]: data,
             "SHA256SUMS.txt": f"{sha}  {c['lib']}\n".encode()}
    if key == "adpkg":
        files["VALIDATION.json"] = (json.dumps({
            "binarySha256": sha,
            "status": "not-revalidated-by-packaging",
            "note": "No device validation evidence is included in this development package.",
        }, indent=2) + "\n").encode()
    if app:
        root = f"/data/data/{app}/files/contents/adrenotools/{name}"
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
Fallback (wrapper in path): leave VK_ICD_FILENAMES unset and pick "{name}" as Graphics Driver Version.
Check: wine log / logcat shows driverInfo "{check}"; .so sha256 {sha}
""").encode()
    out = outdir / (f"{zipstem}.adpkg.zip" if key == "adpkg" else f"{zipstem}-{key}.zip")
    if out.exists(): out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for n in files:
            zi = zipfile.ZipInfo(n, (2026, 10, 17, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, files[n])
    print("OK", out)
EOF
echo "LAUNCHER-ZIPS OK sha256=$(sha256sum "$SO" | cut -d' ' -f1)"
