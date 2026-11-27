#!/usr/bin/env python3
"""Attach same-commit CI development binaries to an existing published release."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time
from urllib.parse import quote
import zipfile

from build_provenance import binary_build_id, validate_source_run
from driver_identity import identity_for_pin


ROOT = Path(__file__).resolve().parents[1]
BUILD_WAIT_SECONDS = 90 * 60


def api(endpoint, paginate=False):
    command = ["gh", "api", endpoint]
    if paginate:
        command.extend(("--paginate", "--slurp"))
    return json.loads(subprocess.check_output(command, text=True))


def matches_source(run, repository, commit):
    return (
        run.get("head_sha") == commit
        and run.get("event") in ("push", "workflow_dispatch")
        and (run.get("head_repository") or {}).get("full_name") == repository
    )


def select_run(runs, repository, commit):
    for run in runs:
        if (
            (run.get("status"), run.get("conclusion")) == ("completed", "success")
            and matches_source(run, repository, commit)
        ):
            validate_source_run(run, repository, commit)
            return run
    raise ValueError(
        f"no successful push/manual build for tag commit {commit}; "
        "finish the build, then rerun release-assets"
    )


def wait_for_run(repository, commit):
    deadline = time.monotonic() + BUILD_WAIT_SECONDS
    while True:
        pages = api(
            f"repos/{repository}/actions/workflows/build.yml/runs?head_sha={commit}&per_page=100",
            paginate=True,
        )
        runs = [
            run for page in pages for run in page["workflow_runs"]
            if matches_source(run, repository, commit)
        ]
        if any((run.get("status"), run.get("conclusion")) == ("completed", "success")
               for run in runs):
            return select_run(runs, repository, commit)
        active = [
            run for run in runs
            if run.get("status") in ("queued", "in_progress", "waiting", "pending", "requested")
        ]
        if not active:
            return select_run(runs, repository, commit)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError(f"timed out waiting for build of tag commit {commit}")
        ids = ", ".join(str(run["id"]) for run in active)
        print(f"Waiting for build of {commit}: active runs {ids}", flush=True)
        time.sleep(min(30, remaining))


def select_artifacts(artifacts, commit):
    selected = {}
    for abi in ("android", "glibc"):
        name = f"g615-dev-{abi}-{commit}"
        matches = [artifact for artifact in artifacts if artifact.get("name") == name]
        if len(matches) != 1 or matches[0].get("expired") is not False:
            raise ValueError(f"expected one non-expired artifact {name}")
        selected[abi] = matches[0]
    return selected


def validate_bundle(path, abi, commit, run_id, lock):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        expected_files = {
            "libvulkan_panfrost.so", "series-manifest.json", "CI-BUILD.json", "SHA256SUMS.txt",
        }
        if abi == "glibc":
            expected_files.add("panfrost_icd.aarch64.json")
        if len(names) != len(set(names)) or set(names) != expected_files:
            raise ValueError(f"unexpected, missing or duplicate files in {path.name}")
        if any(stat.S_ISLNK(info.external_attr >> 16) for info in archive.infolist()):
            raise ValueError(f"symlink in {path.name}")
        if archive.testzip() is not None:
            raise ValueError(f"corrupt ZIP: {path.name}")
        binary = archive.read("libvulkan_panfrost.so")
        record = json.loads(archive.read("CI-BUILD.json"))
        expected = {
            "profile": "g615-v11-csf", "panArch": 11, "frontend": "CSF",
            "abi": "android-aarch64-bionic" if abi == "android" else "linux-aarch64-glibc",
            "projectCommit": commit, "githubRunId": str(run_id), "releaseTier": "dev",
            "mesaCommit": lock["mesaCommit"], "patchSeriesId": lock["patchSeriesId"],
            "binarySha256": hashlib.sha256(binary).hexdigest(),
            "seriesManifestSha256": hashlib.sha256(archive.read("series-manifest.json")).hexdigest(),
            "buildId": binary_build_id(binary),
        }
        for key, value in expected.items():
            if record.get(key) != value:
                raise ValueError(f"{path.name}: CI-BUILD.{key} does not identify this dev build")
        gates = record.get("gates")
        if not isinstance(gates, dict) or any(gates.get(key) != "PASS" for key in ("build", "elf")):
            raise ValueError(f"{path.name}: build and ELF gates must pass")
        checksum = f"{expected['binarySha256']}  libvulkan_panfrost.so\n"
        if archive.read("SHA256SUMS.txt").decode() != checksum:
            raise ValueError(f"{path.name}: binary checksum mismatch")
        if abi == "glibc":
            icd = json.loads(archive.read("panfrost_icd.aarch64.json"))
            if icd["ICD"]["library_path"] != "./libvulkan_panfrost.so":
                raise ValueError(f"{path.name}: ICD must use the adjacent library")
        identity_for_pin(binary, lock)
    return binary


def download_artifact(repository, artifact, path):
    artifact_id = int(artifact["id"])
    with path.open("xb") as output:
        subprocess.run(
            ["gh", "api", f"repos/{repository}/actions/artifacts/{artifact_id}/zip"],
            stdout=output, check=True,
        )


def package_drivers(stage, lock, tag, commit):
    version = re.fullmatch(
        r"(?:panvk-g615-v11-csf-)?v?([0-9]+\.[0-9]+\.[0-9]+)(?:-[A-Za-z0-9.-]+)?", tag
    )
    if version is None:
        raise ValueError("driver packages require a versioned release tag, such as 1.0.0")
    version = f"v{version[1]}-dev.{commit}"
    lock_path = stage / "sources.lock"
    lock_path.write_text(json.dumps(lock))
    output = stage / "drivers"
    subprocess.run([
        str(ROOT / "scripts/package-launcher-zips.sh"),
        "--so", str(stage / "android/libvulkan_panfrost.so"),
        "--ci-android-stage", str(stage / "android"),
        "--ci-glibc-stage", str(stage / "glibc"),
        "--source-lock", str(lock_path), "--outdir", str(output), "--version", version,
    ], check=True)
    expected_names = set()
    for abi in ("android", "glibc"):
        identity = identity_for_pin((stage / abi / "libvulkan_panfrost.so").read_bytes(), lock)
        stem = "Mesa-PanVK" if identity["style"] == "upstream" else "PanVK-Kbase"
        if abi == "android":
            stem += "-Android"
        stem = f"{stem}-{version}-{identity['sha8']}"
        if abi == "glibc":
            expected_names.add(f"{stem}-EMULATOR.zip")
        else:
            expected_names.add(f"{stem}.adpkg.zip")
            expected_names.update(f"{stem}-{launcher}.zip" for launcher in (
                "adrenotools", "winlator", "bannerlator", "cmod", "ludashi", "gamehub",
            ))
    packages = sorted(output.glob("*.zip"))
    if {path.name for path in packages} != expected_names:
        raise ValueError("packager did not generate all eight expected driver imports")
    for path in packages:
        abi = "glibc" if path.name.endswith("-EMULATOR.zip") else "android"
        binary = (stage / abi / "libvulkan_panfrost.so").read_bytes()
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if not names or names[0] != "meta.json" or len(names) != len(set(names)) \
                    or any("/" in name for name in names) or archive.testzip() is not None:
                raise ValueError(f"invalid flat import layout: {path.name}")
            meta = json.loads(archive.read("meta.json"))
            record_bytes = (stage / abi / "CI-BUILD.json").read_bytes()
            record = json.loads(record_bytes)
            library = "libvulkan_freedreno.so" if path.name.endswith("-gamehub.zip") \
                else "libvulkan_panfrost.so"
            if meta.get("libraryName") != library or archive.read(library) != binary \
                    or meta.get("abi") != record["abi"] or meta.get("releaseTier") != "dev" \
                    or meta.get("packageVersion") != version.removeprefix("v"):
                raise ValueError(f"incorrect driver metadata or ABI payload: {path.name}")
            if archive.read("CI-BUILD.json") != record_bytes \
                    or archive.read("series-manifest.json") != \
                    (stage / abi / "series-manifest.json").read_bytes():
                raise ValueError(f"package changed CI provenance: {path.name}")
            if abi == "android" and meta.get("minApi") != record["androidApi"]:
                raise ValueError(f"package does not advertise its built Android API: {path.name}")
            checksum = f"{hashlib.sha256(binary).hexdigest()}  {library}\n"
            if archive.read("SHA256SUMS.txt").decode() != checksum:
                raise ValueError(f"import package checksum mismatch: {path.name}")
    return packages


def upload_assets(repository, tag):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or not tag:
        raise ValueError("repository and release tag are required")
    prefix = f"repos/{repository}"
    release = api(f"{prefix}/releases/tags/{quote(tag, safe='')}")
    if release.get("draft") is not False:
        raise ValueError("publish the release before attaching development assets")
    commit = api(f"{prefix}/commits/{quote(tag, safe='')}")["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("release tag did not resolve to a Git commit")
    run = wait_for_run(repository, commit)
    pages = api(f"{prefix}/actions/runs/{run['id']}/artifacts?per_page=100", paginate=True)
    artifacts = select_artifacts(
        [artifact for page in pages for artifact in page["artifacts"]], commit
    )
    content = api(f"{prefix}/contents/sources.lock?ref={commit}")
    lock = json.loads(base64.b64decode(content["content"], validate=False))
    with tempfile.TemporaryDirectory(prefix="panvk-release-dev-") as directory:
        stage = Path(directory)
        assets = []
        for abi, artifact in artifacts.items():
            archive = stage / f"{artifact['name']}.zip"
            download_artifact(repository, artifact, archive)
            binary = validate_bundle(archive, abi, commit, run["id"], lock)
            abi_stage = stage / abi
            abi_stage.mkdir()
            with zipfile.ZipFile(archive) as bundle:
                for name in bundle.namelist():
                    (abi_stage / name).write_bytes(bundle.read(name))
            raw = stage / f"libvulkan_panfrost-g615-v11-csf-dev-{abi}-aarch64-{commit}.so"
            raw.write_bytes(binary)
            subprocess.run(
                [str(ROOT / "scripts/validate-binary.sh"), "--abi", abi, str(raw)], check=True
            )
            assets.append(raw)
        assets.extend(package_drivers(stage, lock, tag, commit))
        sums = stage / f"g615-dev-{commit}-drivers-SHA256SUMS.txt"
        sums.write_text("".join(
            f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in assets
        ))
        assets.append(sums)
        pages = api(f"{prefix}/releases/{release['id']}/assets?per_page=100", paginate=True)
        existing = {asset["name"]: asset for page in pages for asset in page}
        missing = []
        for path in assets:
            if path.name not in existing:
                missing.append(path)
            elif existing[path.name].get("digest") != \
                    "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest():
                raise ValueError(f"refusing to overwrite existing asset: {path.name}")
        if api(f"{prefix}/commits/{quote(tag, safe='')}")["sha"] != commit:
            raise ValueError("release tag moved while preparing development assets")
        if not missing:
            print(f"All {len(assets)} verified development assets are already attached")
            return
        subprocess.run(
            ["gh", "release", "upload", tag, "--repo", repository, *map(str, missing)],
            check=True,
        )
        print(f"Attached {len(missing)} development assets from run {run['id']} ({commit})")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()
    try:
        upload_assets(args.repository, args.tag)
    except (ValueError, zipfile.BadZipFile) as error:
        parser.exit(1, f"FAIL: {error}\n")


if __name__ == "__main__":
    main()
