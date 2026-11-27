import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class ReleaseCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "release_candidate", ROOT / "scripts/validate-release-candidate.py"
        )
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dist = self.root / "dist"
        self.dist.mkdir()
        self.tag = "panvk-g615-v11-csf-v27.0.0-beta.1"
        self.lock = json.loads((ROOT / "sources.lock").read_text())
        (self.root / "sources.lock").write_text(json.dumps(self.lock))
        self.binary = (
            f"\0Mesa {self.lock['mesaVersion']} "
            f"(git-{self.lock['mesaCommit'][:10]})\0driver"
        ).encode()
        self.sha8 = self.lock["mesaCommit"][:8]
        self.records = {}
        for abi, suffix in (("android", ".adpkg.zip"), ("glibc", "-EMULATOR.zip")):
            stem = "Mesa-PanVK-Android" if abi == "android" else "Mesa-PanVK"
            name = f"{stem}-v27.0.0-beta.1-{self.sha8}{suffix}"
            self.records[abi] = {
                "profile": "g615-v11-csf",
                "abi": "android-aarch64-bionic" if abi == "android" else "linux-aarch64-glibc",
                "mesaCommit": self.lock["mesaCommit"], "patchSeriesId": self.lock["patchSeriesId"],
                "variant": "default", "seriesManifestSha256": "fixture-series",
                "binarySha256": hashlib.sha256(self.binary).hexdigest(), "buildId": "fixture-id",
            }
            self.write_package(name, self.binary, {
                "packageVersion": "27.0.0-beta.1", "profile": "g615-v11-csf",
                "panArch": 11, "frontend": "CSF", "libraryName": "libvulkan_panfrost.so",
                "abi": "android-aarch64-bionic" if abi == "android" else "linux-aarch64-glibc",
            })
            (self.dist / f"libvulkan_panfrost-g615-v11-csf-{abi}-aarch64.so").write_bytes(self.binary)
        for launcher in self.module.LAUNCHERS:
            self.write_package(
                f"Mesa-PanVK-Android-v27.0.0-beta.1-{self.sha8}-{launcher}.zip",
                self.binary, {
                    "packageVersion": "27.0.0-beta.1", "profile": "g615-v11-csf",
                    "panArch": 11, "frontend": "CSF", "libraryName": "libvulkan_panfrost.so",
                },
            )
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Fixture"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "fixture@example.invalid"], check=True)
        self.images = []
        for role in ("panprobe", "panplay"):
            image = self.root / f"{role}.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\nfixture")
            self.images.append({
                "path": image.name, "role": role, "panArch": 11, "androidApi": 36,
            })
            subprocess.run(["git", "-C", str(self.root), "add", image.name], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "screenshots"], check=True)
        commit = subprocess.check_output(
            ["git", "-C", str(self.root), "rev-parse", "HEAD"], text=True
        ).strip()
        for abi, record in self.records.items():
            data = {
                **record, "projectCommit": commit,
                "toolchain": {name: "recorded version" for name in (
                    "compiler", "hostCompiler", "llvm", "rust", "bindgen", "meson", "ninja",
                    "hostSpirvToolsCommit", "hostSpirvHeadersCommit",
                )},
                "host": "fixture host", "androidApi": 35,
                "ndkProperties": "Pkg.Revision = 30.0.16248370",
            }
            (self.dist / f"CI-BUILD-{abi}.json").write_text(json.dumps(data))
        (self.dist / "release-screenshots.json").write_text(json.dumps({"screenshots": self.images}))

    def write_package(self, name, binary, meta):
        with zipfile.ZipFile(self.dist / name, "w") as package:
            package.writestr("meta.json", json.dumps(meta))
            package.writestr(meta["libraryName"], binary)
            if meta.get("abi"):
                abi = "android" if meta["abi"] == "android-aarch64-bionic" else "glibc"
                package.writestr("MANIFEST.json", json.dumps(self.records[abi]))

    def validate(self):
        with patch.object(self.module, "validate_canonical_package") as validator:
            result = self.module.validate_release(
                self.root, self.dist, self.tag, "owner/project"
            )
            self.assertEqual(validator.call_count, 2)
            return result

    def test_valid_bundle_publishes_only_selected_assets_and_images_first(self):
        (self.dist / "unrelated.txt").write_text("not a release asset")
        result = self.validate()
        self.assertEqual(len(result["assets"]), 14)
        self.assertFalse(any(path.endswith("unrelated.txt") for path in result["assets"]))
        self.assertTrue(result["notes"].startswith("![PanProbe"))
        self.assertIn("PanPlay DXVK cube", result["notes"])
        self.assertIn("PAN_ARCH=11, Android API 36", result["notes"])

    def test_clean_runner_without_packages_fails(self):
        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaisesRegex(ValueError, "exactly one"):
                self.module.validate_release(self.root, Path(empty), self.tag, "owner/project")

    def test_package_version_cannot_be_promoted_by_tag(self):
        self.tag = "panvk-g615-v11-csf-v27.0.0"
        with self.assertRaisesRegex(ValueError, "version"):
            self.validate()

    def test_raw_asset_must_match_packaged_binary(self):
        (self.dist / "libvulkan_panfrost-g615-v11-csf-android-aarch64.so").write_bytes(b"another")
        with self.assertRaisesRegex(ValueError, "binary"):
            self.validate()

    def test_launcher_cannot_contain_another_binary(self):
        name = next(self.dist.glob("*-gamehub.zip"))
        self.write_package(name.name, b"another", {
            "packageVersion": "27.0.0-beta.1", "profile": "g615-v11-csf",
            "panArch": 11, "frontend": "CSF", "libraryName": "libvulkan_freedreno.so",
        })
        with self.assertRaisesRegex(ValueError, "binary"):
            self.validate()

    def test_canonical_package_cannot_claim_another_frontend(self):
        package = next(self.dist.glob("*.adpkg.zip"))
        with zipfile.ZipFile(package) as archive:
            meta = json.loads(archive.read("meta.json"))
        meta["frontend"] = "JM"
        self.write_package(package.name, self.binary, meta)
        with self.assertRaisesRegex(ValueError, "CSF"):
            self.validate()

    def test_stable_still_requires_launchers(self):
        next(self.dist.glob("*-gamehub.zip")).unlink()
        self.tag = "panvk-g615-v11-csf-v27.0.0"
        for package in self.dist.glob("*.zip"):
            with zipfile.ZipFile(package) as archive:
                meta = json.loads(archive.read("meta.json"))
            meta["packageVersion"] = "27.0.0"
            stem = package.name.replace("-v27.0.0-beta.1-", "-v27.0.0-")
            package.unlink()
            self.write_package(stem, self.binary, meta)
        with self.assertRaisesRegex(ValueError, "gamehub"):
            self.validate()

    def test_changed_or_uncommitted_screenshot_is_rejected(self):
        (self.root / "panprobe.png").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "committed"):
            self.validate()

    def test_canonical_validation_failures_are_not_swallowed(self):
        with patch.object(
            self.module, "validate_canonical_package",
            side_effect=subprocess.CalledProcessError(1, "validate-package.sh"),
        ):
            with self.assertRaises(subprocess.CalledProcessError):
                self.module.validate_release(self.root, self.dist, self.tag, "owner/project")

    def test_build_record_must_identify_binary_and_record_toolchain(self):
        path = self.dist / "CI-BUILD-android.json"
        record = json.loads(path.read_text())
        for changes in (
            {"binarySha256": "another binary"}, {"toolchain": {}},
            {"projectCommit": "another commit"},
        ):
            with self.subTest(changes=changes):
                path.write_text(json.dumps({**record, **changes}))
                with self.assertRaisesRegex(ValueError, "build record"):
                    self.validate()

    def test_source_run_must_be_successful_same_commit_and_not_a_fork_or_pr(self):
        run = {
            "status": "completed", "conclusion": "success", "head_sha": "a" * 40,
            "event": "workflow_dispatch", "head_repository": {"full_name": "owner/project"},
        }
        self.module.validate_source_run(run, "owner/project", "a" * 40)
        for changes in (
            {"head_sha": "b" * 40}, {"conclusion": "failure"},
            {"event": "pull_request"}, {"head_repository": {"full_name": "fork/project"}},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module.validate_source_run({**run, **changes}, "owner/project", "a" * 40)

    def test_invalid_or_historical_tags_are_rejected(self):
        for tag in ("panvk-kbase-v27.0.0", "panvk-g615-v11-csf-v27.0.0-betaXYZ", "../tag"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                self.module.release_tag(tag)


if __name__ == "__main__":
    unittest.main()
