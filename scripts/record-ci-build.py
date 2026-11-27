#!/usr/bin/env python3
"""Record a development ICD's inputs and toolchain, without runtime claims."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from build_provenance import binary_build_id, checked_series
from driver_identity import identity_for_pin


ROOT = Path(__file__).resolve().parents[1]


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--abi", required=True, choices=("android", "glibc"))
    parser.add_argument("--stage", required=True, type=Path)
    args = parser.parse_args()
    lock = json.loads((ROOT / "sources.lock").read_text())
    psid = command("python3", str(ROOT / "scripts/compute-patch-series-id.py"),
                   "--profile", "g615-v11-csf")
    if psid != lock["patchSeriesId"]:
        parser.error("sources.lock patchSeriesId does not match the current inventory")
    series, digest = checked_series(ROOT, (args.stage / "series-manifest.json").read_bytes())
    command(str(ROOT / "scripts/validate-binary.sh"), "--abi", args.abi,
            str(args.stage / "libvulkan_panfrost.so"))
    binary = (args.stage / "libvulkan_panfrost.so").read_bytes()
    identity = identity_for_pin(binary, lock)
    compiler = "aarch64-linux-gnu-gcc"
    ndk = None
    api = None
    if args.abi == "android":
        ndk = Path(os.environ["ANDROID_NDK_ROOT"])
        api = int(os.environ["ANDROID_API"])
        compiler = str(ndk / "toolchains/llvm/prebuilt/linux-x86_64/bin" /
                       f"aarch64-linux-android{api}-clang")
    tools = {
        name: command(*cmd) for name, cmd in {
            "compiler": (compiler, "--version"),
            "hostCompiler": ("cc", "--version"),
            "llvm": ("llvm-config", "--version"),
            "rust": ("rustc", "--version", "--verbose"),
            "bindgen": ("bindgen", "--version"),
            "meson": ("meson", "--version"),
            "ninja": ("ninja", "--version"),
            "hostSpirvToolsCommit": ("git", "-C", str(ROOT / "work/ci-spirv-tools"), "rev-parse", "HEAD"),
            "hostSpirvHeadersCommit": ("git", "-C", str(ROOT / "work/ci-spirv-tools/external/spirv-headers"),
                                      "rev-parse", "HEAD"),
        }.items()
    }
    data = {
        "profile": "g615-v11-csf", "panArch": 11, "frontend": "CSF",
        "abi": "android-aarch64-bionic" if args.abi == "android" else "linux-aarch64-glibc",
        "mesaCommit": lock["mesaCommit"], "mesaVersion": lock["mesaVersion"],
        "patchSeriesId": psid, "variant": series["variant"],
        "seriesManifestSha256": digest,
        "binarySha256": hashlib.sha256(binary).hexdigest(),
        "buildId": binary_build_id(binary), "driverInfo": identity["driverInfo"],
        "projectCommit": command("git", "-C", str(ROOT), "rev-parse", "HEAD"),
        "githubRunId": os.environ["GITHUB_RUN_ID"],
        "githubRunAttempt": os.environ["GITHUB_RUN_ATTEMPT"],
        "host": command("uname", "-a"), "toolchain": tools,
        "androidApi": api,
        "ndkProperties": (ndk / "source.properties").read_text() if ndk else None,
        "gates": {"build": "PASS", "elf": "PASS", "runtime": "NOT EXECUTED",
                  "stability": "NOT EXECUTED", "performance": "NOT EXECUTED"},
        "releaseTier": "dev",
    }
    with (args.stage / "CI-BUILD.json").open("x") as out:
        out.write(json.dumps(data, indent=2) + "\n")
    with (args.stage / "SHA256SUMS.txt").open("x") as out:
        out.write(f"{data['binarySha256']}  libvulkan_panfrost.so\n")
    print(f"CI-BUILD: recorded {data['abi']} {data['binarySha256']}")


if __name__ == "__main__":
    main()
