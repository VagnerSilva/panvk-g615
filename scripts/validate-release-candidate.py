#!/usr/bin/env python3
"""Validate manually supplied G615 release assets before publication."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import quote
import zipfile

from driver_identity import identity_for_pin
from build_provenance import validate_source_run


LAUNCHERS = ("adrenotools", "winlator", "bannerlator", "cmod", "ludashi", "gamehub")
ROOT = Path(__file__).resolve().parents[1]


def release_tag(tag):
    match = re.fullmatch(
        r"panvk-g615-v11-csf-v([0-9]+\.[0-9]+\.[0-9]+(?:-(dev|alpha|beta|rc)(?:\.[0-9]+)?)?)",
        tag,
    )
    if not match:
        raise ValueError("only versioned panvk-g615-v11-csf-v tags are supported")
    tier = match[2] or "stable"
    return {"tag": tag, "version": match[1], "tier": tier, "prerelease": tier != "stable"}


def validate_canonical_package(root, package, abi, raw):
    subprocess.run([str(root / "scripts/validate-package.sh"), str(package)], check=True)
    subprocess.run(
        [str(root / "scripts/validate-binary.sh"), "--abi", abi, str(raw)], check=True
    )


def one_package(dist, pattern):
    paths = sorted(dist.glob(pattern))
    if len(paths) != 1:
        raise ValueError(f"expected exactly one {pattern}, found {len(paths)}")
    if paths[0].is_symlink():
        raise ValueError(f"release package must not be a symlink: {paths[0]}")
    return paths[0]


def package_payload(path, version):
    with zipfile.ZipFile(path) as package:
        if len(package.namelist()) != len(set(package.namelist())):
            raise ValueError(f"duplicate ZIP entries in {path.name}")
        if package.testzip() is not None:
            raise ValueError(f"corrupt ZIP: {path.name}")
        meta = json.loads(package.read("meta.json"))
        if meta.get("packageVersion") != version:
            raise ValueError(f"package version does not match tag: {path.name}")
        if meta.get("profile") != "g615-v11-csf":
            raise ValueError(f"package is not G615: {path.name}")
        return meta, package.read(meta["libraryName"])


def validate_build_record(root, dist, abi, package, payload):
    path = dist / f"CI-BUILD-{abi}.json"
    if path.is_symlink():
        raise ValueError(f"build record must not be a symlink: {path.name}")
    record = json.loads(path.read_text())
    with zipfile.ZipFile(package) as archive:
        manifest = json.loads(archive.read("MANIFEST.json"))
    expected = {key: manifest.get(key) for key in (
        "profile", "abi", "mesaCommit", "patchSeriesId", "variant",
        "seriesManifestSha256", "binarySha256", "buildId",
    )}
    expected["binarySha256"] = hashlib.sha256(payload).hexdigest()
    expected["projectCommit"] = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    for key, value in expected.items():
        if not isinstance(value, str) or not value or record.get(key) != value:
            raise ValueError(f"build record {path.name}.{key} does not identify this artifact")
    tools = record.get("toolchain")
    if not isinstance(tools, dict) or any(
        not isinstance(tools.get(key), str) or not tools[key].strip()
        for key in ("compiler", "hostCompiler", "llvm", "rust", "bindgen", "meson", "ninja",
                    "hostSpirvToolsCommit", "hostSpirvHeadersCommit")
    ) or not isinstance(record.get("host"), str) or not record["host"].strip():
        raise ValueError(f"build record {path.name} lacks the recorded host/toolchain")
    if abi == "android" and (
        type(record.get("androidApi")) is not int or record["androidApi"] <= 0
        or not isinstance(record.get("ndkProperties"), str) or not record["ndkProperties"].strip()
    ):
        raise ValueError(f"build record {path.name} lacks the actual Android API/NDK")
    return str(path.resolve())


def screenshots(root, dist, repository, tag):
    data = json.loads((dist / "release-screenshots.json").read_text())
    images = data["screenshots"]
    if not isinstance(images, list) or not images:
        raise ValueError("release-screenshots.json must list the latest PanProbe and PanPlay screenshots")
    assets, notes, urls, roles = [], [], [], set()
    for image in images:
        role = image["role"]
        if role not in ("panprobe", "panplay"):
            raise ValueError(f"unknown screenshot role: {role}")
        relative = Path(image["path"])
        if (relative.is_absolute() or ".." in relative.parts
                or "\n" in str(relative) or "\r" in str(relative)
                or relative.suffix.lower() not in (".png", ".jpg", ".jpeg")):
            raise ValueError(f"invalid screenshot path: {relative}")
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"missing committed screenshot: {relative}")
        committed = subprocess.check_output(
            ["git", "-C", str(root), "show", f"HEAD:{relative.as_posix()}"]
        )
        if path.read_bytes() != committed:
            raise ValueError(f"screenshot differs from committed image: {relative}")
        if image.get("panArch") != 11 or type(image.get("androidApi")) is not int or image["androidApi"] < 35:
            raise ValueError(f"screenshot needs PAN_ARCH=11 and actual Android API >=35: {relative}")
        label = "PanProbe" if role == "panprobe" else "PanPlay DXVK cube (HUD)"
        url = f"https://raw.githubusercontent.com/{repository}/{quote(tag, safe='')}/{quote(relative.as_posix(), safe='/')}"
        notes.extend([f"![{label}]({url})", f"{label}: PAN_ARCH=11, Android API {image['androidApi']}.", ""])
        assets.append(str(path.resolve()))
        urls.append(url)
        roles.add(role)
    if roles != {"panprobe", "panplay"}:
        raise ValueError("screenshots must include both PanProbe and PanPlay DXVK cube with HUD")
    return assets, notes, urls


def validate_release(root, dist, tag, repository):
    meta_tag = release_tag(tag)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("invalid GitHub repository")
    lock = json.loads((root / "sources.lock").read_text())
    assets = []
    android = None
    sha8 = None
    for abi, pattern, expected_abi, stem, suffix in (
        ("android", "*.adpkg.zip", "android-aarch64-bionic", "Mesa-PanVK-Android", ".adpkg.zip"),
        ("glibc", "*-EMULATOR.zip", "linux-aarch64-glibc", "Mesa-PanVK", "-EMULATOR.zip"),
    ):
        package = one_package(dist, pattern)
        meta, payload = package_payload(package, meta_tag["version"])
        if meta.get("abi") != expected_abi or meta["libraryName"] != "libvulkan_panfrost.so":
            raise ValueError(f"wrong canonical ABI/library: {package.name}")
        if (meta.get("panArch"), meta.get("frontend")) != (11, "CSF"):
            raise ValueError(f"canonical package is not G615 CSF v11: {package.name}")
        identity = identity_for_pin(payload, lock)
        expected_name = f"{stem}-v{meta_tag['version']}-{identity['sha8']}{suffix}"
        if package.name != expected_name:
            raise ValueError(f"package filename/version must be {expected_name}")
        raw = dist / f"libvulkan_panfrost-g615-v11-csf-{abi}-aarch64.so"
        if raw.is_symlink() or raw.read_bytes() != payload:
            raise ValueError(f"raw binary does not match package: {raw.name}")
        validate_canonical_package(root, package, abi, raw)
        record = validate_build_record(root, dist, abi, package, payload)
        assets.extend((str(raw.resolve()), str(package.resolve()), record))
        if abi == "android":
            android = hashlib.sha256(payload).hexdigest()
            sha8 = identity["sha8"]
    for launcher in LAUNCHERS:
        matches = list(dist.glob(f"*-{launcher}.zip"))
        if not matches and meta_tag["tier"] in ("dev", "alpha"):
            continue
        package = one_package(dist, f"*-{launcher}.zip")
        meta, payload = package_payload(package, meta_tag["version"])
        if (meta.get("panArch"), meta.get("frontend")) != (11, "CSF"):
            raise ValueError(f"launcher is not G615 CSF v11: {package.name}")
        if hashlib.sha256(payload).hexdigest() != android:
            raise ValueError(f"launcher contains another binary: {package.name}")
        expected = f"Mesa-PanVK-Android-v{meta_tag['version']}-{sha8}-{launcher}.zip"
        if package.name != expected:
            raise ValueError(f"launcher filename/version must be {expected}")
        assets.append(str(package.resolve()))
    image_assets, notes, urls = screenshots(root, dist, repository, tag)
    assets.extend(image_assets)
    if len({Path(path).name for path in assets}) != len(assets):
        raise ValueError("release asset filenames must be unique")
    notes.extend([
        "Mali-G615 CSF v11 / Kbase only. See each package's binary-specific validation.",
        "Not Vulkan-conformant. Not universal Mali support.",
        "No Samba S3/Bachata/Winlator/GameHub validation is claimed beyond the recorded tests.",
        "", f"tier={meta_tag['tier']} prerelease={str(meta_tag['prerelease']).lower()}",
    ])
    return {**meta_tag, "assets": assets, "notes": "\n".join(notes) + "\n", "imageUrls": urls}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    tag_parser = commands.add_parser("tag")
    tag_parser.add_argument("--tag", required=True)
    tag_parser.add_argument("--github-output", required=True, type=Path)
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--file", required=True, type=Path)
    run_parser.add_argument("--repository", required=True)
    run_parser.add_argument("--commit", required=True)
    package_parser = commands.add_parser("packages")
    package_parser.add_argument("--tag", required=True)
    package_parser.add_argument("--dist", required=True, type=Path)
    package_parser.add_argument("--repository", required=True)
    package_parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "tag":
            data = release_tag(args.tag)
            with args.github_output.open("a") as out:
                for key, value in data.items():
                    out.write(f"{key}={str(value).lower() if isinstance(value, bool) else value}\n")
        elif args.command == "run":
            validate_source_run(json.loads(args.file.read_text()), args.repository, args.commit)
        else:
            data = validate_release(ROOT, args.dist, args.tag, args.repository)
            with args.out.open("x") as out:
                out.write(json.dumps(data, indent=2) + "\n")
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        parser.exit(1, f"RELEASE-VALIDATION: FAIL {error}\n")
    print("RELEASE-VALIDATION: PASS")


if __name__ == "__main__":
    main()
