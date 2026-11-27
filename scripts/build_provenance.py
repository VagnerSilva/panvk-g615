"""Ordered G615 build inputs and binary-specific package provenance."""
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path


PASS_GATE_STATUSES = ("pass", "passed", "ok", "true")


def validate_source_run(run, repository, commit):
    if (run.get("status"), run.get("conclusion")) != ("completed", "success"):
        raise ValueError("source run must have completed successfully")
    if run.get("head_sha") != commit:
        raise ValueError("source run commit does not match the release tag")
    if run.get("event") not in ("push", "workflow_dispatch"):
        raise ValueError("source run must be a push or manual run, not a PR")
    if (run.get("head_repository") or {}).get("full_name") != repository:
        raise ValueError("source run must belong to this repository, not a fork")


def gate_status(evidence):
    if isinstance(evidence, dict):
        evidence = evidence.get("result") or evidence.get("status") or evidence.get("state") or "untested"
    return str(evidence if evidence is not None else "untested").lower()


def series_manifest(root, profile, variant):
    root = Path(root)
    if profile != "g615-v11-csf":
        raise ValueError("only g615-v11-csf is supported")
    config = json.loads((root / "profiles" / f"{profile}.json").read_text())
    if (config["panArch"], config["frontend"], config["kernelInterface"]) != (11, "CSF", "mali_kbase"):
        raise ValueError("invalid G615 profile: requires v11, CSF and mali_kbase")
    if variant not in ("default", "kbase-sync-002-004"):
        raise ValueError(f"unsupported series variant: {variant}")
    families = ["common", "android", "kbase-common", "app-loader", "wsi", "csf", "csf-v11",
                "experimental-kbase-sync"]
    inputs = []
    for family in families:
        directory = root / "patches" / family
        for path in sorted(directory.glob("*.patch")):
            if family == "experimental-kbase-sync" and path.name not in {
                "002-android-release-queue-mesa27.patch",
                "003-kbase-coalesce-mem-sync.patch",
                "004-kbase-sync-file-waiter-lifetime.patch",
                "005-kbase-avoid-wait-any-spin.patch",
                "007-kbase-sync-file-poll-deadlines.patch",
                "008-kbase-shared-group-csg-sync.patch",
            }:
                continue
            inputs.append(path)
        overlay = directory / "files"
        inputs.extend(sorted(p for p in overlay.rglob("*")
                             if p.is_file() and not p.is_symlink() and p.name != "README"))
    return {
        "mesaCommit": json.loads((root / "sources.lock").read_text())["mesaCommit"],
        "profile": profile, "variant": variant,
        "inputs": [{"path": p.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs],
    }


def checked_series(root, content):
    data = json.loads(content)
    expected = series_manifest(root, data["profile"], data["variant"])
    if data != expected:
        raise ValueError("applied-input manifest does not match the selected G615 series")
    return data, hashlib.sha256(content).hexdigest()


def binary_build_id(content):
    with tempfile.TemporaryDirectory(prefix="panvk-build-id-") as temp:
        so = Path(temp) / "driver.so"
        so.write_bytes(content)
        output = subprocess.check_output(["readelf", "-n", str(so)], text=True)
    match = re.search(r"Build ID: ([0-9a-fA-F]+)", output)
    if match is None:
        raise ValueError("binary has no GNU Build ID")
    return match.group(1).lower()


def validate_artifact_provenance(root, read, manifest, source, validation, abi, profile, sha, resolved_gates):
    series, digest = checked_series(root, read("series-manifest.json"))
    expected = {
        "profile": profile, "abi": abi, "mesaCommit": series["mesaCommit"],
        "variant": series["variant"], "seriesManifestSha256": digest,
        "binarySha256": sha,
        "patchSeriesId": json.loads((Path(root) / "sources.lock").read_text())["patchSeriesId"],
    }
    build_id = binary_build_id(read("libvulkan_panfrost.so"))
    for name, doc in (("MANIFEST", manifest), ("SOURCE", source)):
        for key, value in {**expected, "buildId": build_id}.items():
            if doc.get(key) != value:
                raise ValueError(f"{name}.{key} does not identify this artifact")
    for key, value in expected.items():
        if validation.get(key) != value:
            raise ValueError(f"VALIDATION.{key} does not identify this artifact")
    section = "android" if abi == "android-aarch64-bionic" else "glibc"
    section_evidence = validation.get(section, {})
    if not isinstance(section_evidence, dict):
        raise ValueError(f"VALIDATION.{section} must be an object")
    for gate, evidence in {**section_evidence, **resolved_gates}.items():
        if isinstance(evidence, dict):
            if gate_status(evidence) in PASS_GATE_STATUSES and evidence.get("binarySha256") != sha:
                raise ValueError(f"VALIDATION.{section}.{gate} has another binary identity")
