#!/usr/bin/env python3
"""Self-check: scripts/validate-package.sh beta+ gates. No test framework."""
import hashlib, json, shutil, subprocess, sys, tempfile, zipfile, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATE = ROOT / "scripts" / "validate-package.sh"
PIN = json.loads((ROOT / "sources.lock").read_text())["mesaCommit"]
PSID = subprocess.check_output(
    [sys.executable, str(ROOT / "scripts/compute-patch-series-id.py"),
     "--profile", "g615-v11-csf"], text=True).strip()
sys.path.insert(0, str(ROOT / "scripts"))
from build_provenance import series_manifest, binary_build_id

with tempfile.TemporaryDirectory() as fixture_dir:
    fixture_so = pathlib.Path(fixture_dir) / "fixture.so"
    subprocess.run(["cc", "-x", "c", "-shared", "-fPIC", "-Wl,--build-id=sha1",
                    "-o", str(fixture_so), "-"], input="int panvk_package_fixture;\n",
                   text=True, check=True, capture_output=True)
    SO = fixture_so.read_bytes()
SERIES = (json.dumps(series_manifest(ROOT, "g615-v11-csf", "default"),
                     sort_keys=True, indent=2) + "\n").encode()
BUILD_ID = binary_build_id(SO)

def digest(b):
    return hashlib.sha256(b).hexdigest()

def provenance(abi):
    return {"profile": "g615-v11-csf", "abi": abi, "mesaCommit": PIN,
            "patchSeriesId": PSID, "variant": "default",
            "seriesManifestSha256": digest(SERIES), "binarySha256": digest(SO),
            "buildId": BUILD_ID}

def write_zip(path, files):
    with zipfile.ZipFile(path, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)

def run_val(zpath, validator=VALIDATE):
    p = subprocess.run([str(validator), str(zpath)], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr

def android_ok(**overrides):
    sha = digest(SO)
    meta = {
        "schemaVersion": 1, "name": "PanVK", "libraryName": "libvulkan_panfrost.so",
        "abi": "android-aarch64-bionic", "backend": "panvk-kbase",
        "profile": "g615-v11-csf", "sourceCommit": PIN, "patchSeriesId": PSID,
        "packageVersion": "0.1.0-beta.3", "minApi": 35, "prerelease": True,
        "published": False, "bcCompatibility": {"included": False},
    }
    meta.update(overrides.get("meta", {}))
    man = provenance("android-aarch64-bionic")
    man.update(overrides.get("man", {}))
    valid = {
        **provenance("android-aarch64-bionic"),
        "android": {
            "enumeration": "pass", "deviceCreate": "pass", "compute10": "pass",
            "offscreen": "pass", "ahb": "pass", "vulkanSurface": "pass",
            "swapchain300": "pass", "coldSecondLaunch": "pass",
        }
    }
    valid.update(overrides.get("valid", {}))
    files = {
        "libvulkan_panfrost.so": SO,
        "meta.json": json.dumps(meta),
        "MANIFEST.json": json.dumps(man),
        "SOURCE.json": json.dumps(provenance("android-aarch64-bionic")),
        "series-manifest.json": SERIES,
        "VALIDATION.json": json.dumps(valid),
        "SHA256SUMS.txt": f"{sha}  libvulkan_panfrost.so\n",
        "runtime-feature-matrix.json": json.dumps({"gpuId": "0xb8a31030"}),
        "extension-gap.json": json.dumps({"summary": {"runtimeExposed": 194}}),
    }
    files.update(overrides.get("files", {}))
    for k in overrides.get("drop", ()):
        files.pop(k, None)
    return files

def glibc_ok():
    sha = digest(SO)
    return {
        "libvulkan_panfrost.so": SO,
        "panfrost_icd.aarch64.json": json.dumps({"ICD": {"library_path": "libvulkan_panfrost.so"}}),
        "meta.json": json.dumps({
            "schemaVersion": 1, "name": "PanVK", "libraryName": "libvulkan_panfrost.so",
            "abi": "linux-aarch64-glibc", "backend": "panvk-kbase",
            "profile": "g615-v11-csf", "sourceCommit": PIN, "patchSeriesId": PSID,
            "packageVersion": "0.1.0-beta.3", "prerelease": True,
            "published": False, "bcCompatibility": {"included": False},
        }),
        "MANIFEST.json": json.dumps(provenance("linux-aarch64-glibc")),
        "SOURCE.json": json.dumps(provenance("linux-aarch64-glibc")),
        "series-manifest.json": SERIES,
        "VALIDATION.json": json.dumps({**provenance("linux-aarch64-glibc"),
            "glibc": {"enumeration": "pass", "compute10": "pass", "offscreen": "pass"}}),
        "SHA256SUMS.txt": f"{sha}  libvulkan_panfrost.so\n",
        "runtime-feature-matrix.json": json.dumps({"gpuId": "0xb8a31030"}),
        "extension-gap.json": json.dumps({"summary": {"runtimeExposed": 194}}),
    }

def expect(name, files, want_ok, zname="p.zip", validator=VALIDATE):
    with tempfile.TemporaryDirectory() as td:
        z = pathlib.Path(td) / zname
        write_zip(z, files)
        rc, out = run_val(z, validator)
        ok = rc == 0
        if ok != want_ok:
            print(f"FAIL {name}: rc={rc} want_ok={want_ok}\n{out}")
            return 1
        print(f"OK {name} rc={rc}")
        return 0

def main():
    fails = 0
    fails += expect("android-beta-pass", android_ok(), True)
    fails += expect("glibc-beta-pass", glibc_ok(), True)
    for name, evidence, alias in (
        ("uppercase", {"status": "PASS"}, None),
        ("result-precedence", {"result": "PASS", "status": "fail"}, None),
        ("true-result", {"result": True}, None),
        ("flat-alias", {"state": "PASS"}, "glibcCompute"),
    ):
        files = android_ok()
        valid = json.loads(files["VALIDATION.json"])
        evidence = {**evidence, "binarySha256": "ab" * 32}
        if alias:
            del valid["android"]["compute10"]
            valid[alias] = evidence
        else:
            valid["android"]["compute10"] = evidence
        files["VALIDATION.json"] = json.dumps(valid)
        fails += expect(f"stale-gate-{name}", files, False)
    valid = json.loads(android_ok()["VALIDATION.json"])
    valid["android"]["compute10"] = {
        "result": "PASS", "status": "fail", "binarySha256": digest(SO),
    }
    fails += expect("matching-gate-result-precedence", android_ok(valid=valid), True)
    fails += expect("missing-applied-series", android_ok(drop=("series-manifest.json",)), False)
    fails += expect("wrong-validation-binary", android_ok(valid={"binarySha256": "ab" * 32}), False)
    fails += expect("wrong-validation-abi", android_ok(valid={"abi": "linux-aarch64-glibc"}), False)
    fails += expect("wrong-validation-variant", android_ok(valid={"variant": "kbase-sync-002-004"}), False)
    fails += expect("wrong-series-digest", android_ok(man={"seriesManifestSha256": "ab" * 32}), False)
    fails += expect("wrong-build-id", android_ok(man={"buildId": "ab" * 20}), False)
    incomplete = json.loads(SERIES)
    incomplete["inputs"] = incomplete["inputs"][:-1]
    fails += expect("incomplete-applied-series", android_ok(
        files={"series-manifest.json": json.dumps(incomplete)}), False)
    fails += expect("missing-validation", android_ok(drop=("VALIDATION.json",)), False)
    fails += expect("missing-matrix", android_ok(drop=("runtime-feature-matrix.json",)), False)
    fails += expect("short-profile-rejected", android_ok(meta={"profile": "v11-csf"}), False)
    fails += expect("pending-psid", android_ok(meta={"patchSeriesId": "PENDING-P3-REBASE"}), False)
    wrong_psid = "sha256:" + "ab" * 32
    fails += expect("wrong-meta-psid", android_ok(meta={"patchSeriesId": wrong_psid}), False)
    fails += expect("wrong-manifest-psid", android_ok(man={"patchSeriesId": wrong_psid}), False)
    fails += expect("wrong-source-psid", android_ok(files={"SOURCE.json": json.dumps(
        {"mesaCommit": PIN, "patchSeriesId": wrong_psid})}), False)
    fails += expect("missing-source-psid", android_ok(files={"SOURCE.json": json.dumps(
        {"mesaCommit": PIN})}), False)
    fails += expect("missing-manifest-psid", android_ok(man={"patchSeriesId": ""}), False)
    other_profile = "g52-v7-jm"
    other_result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/compute-patch-series-id.py"),
         "--profile", other_profile], text=True, capture_output=True)
    if (other_result.returncode == 0 or
            "only g615-v11-csf is supported" not in other_result.stderr):
        print("FAIL retired-profile-series-id")
        fails += 1
    else:
        print("PASS retired-profile-series-id")
    fails += expect("other-profile-psid", android_ok(
        meta={"profile": other_profile, "patchSeriesId": PSID},
        man={"profile": other_profile, "patchSeriesId": PSID},
        files={"SOURCE.json": json.dumps({"mesaCommit": PIN, "patchSeriesId": PSID})}), False)
    with tempfile.TemporaryDirectory() as td:
        fixture = pathlib.Path(td)
        for directory in ("scripts", "profiles", "patches"):
            shutil.copytree(ROOT / directory, fixture / directory)
        lock = json.loads((ROOT / "sources.lock").read_text())
        lock["patchSeriesId"] = wrong_psid
        (fixture / "sources.lock").write_text(json.dumps(lock))
        fails += expect("stale-lock-psid", android_ok(), False,
                        validator=fixture / "scripts/validate-package.sh")
    fails += expect("wrong-commit", android_ok(meta={"sourceCommit": "deadbeef" * 5}), False)
    fails += expect("untested-gate", android_ok(valid={"android": {
        "enumeration": "untested", "deviceCreate": "pass", "compute10": "pass",
        "offscreen": "pass", "ahb": "pass", "vulkanSurface": "pass",
        "swapchain300": "pass", "coldSecondLaunch": "pass",
    }}), False)
    fails += expect("minapi-29", android_ok(meta={"minApi": 29}), False)
    # "-devel" in an upstream-style name is not the dev tier: an rc package with an untested gate still fails.
    untested_rc = android_ok(meta={"name": "Mesa-PanVK-26.3.0-devel-6a5d4e27", "packageVersion": "0.1.0-rc5"},
                             valid={"android": {"enumeration": "untested"}})
    fails += expect("devel-name-is-rc", untested_rc, False, "Mesa-PanVK-Android-v0.1.0-rc5-26.3.0-devel.adpkg.zip")
    fails += expect("devel-name-rc-pass", android_ok(meta={"packageVersion": "0.1.0-rc5"}), True,
                    "Mesa-PanVK-Android-v0.1.0-rc5-26.3.0-devel.adpkg.zip")
    # A real dev package skips the beta+ gates.
    fails += expect("dev-tier-skips-gates", android_ok(meta={"packageVersion": "0.0.0-dev"}, drop=("VALIDATION.json",)),
                    True, "Mesa-PanVK-Android-v0.0.0-dev-6a5d4e27.adpkg.zip")
    bad_sha = android_ok()
    bad_sha["SHA256SUMS.txt"] = ("0" * 64) + "  libvulkan_panfrost.so\n"
    fails += expect("sha-mismatch", bad_sha, False)
    if fails:
        print(f"SELFCHECK FAIL {fails}")
        return 1
    print("SELFCHECK PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
