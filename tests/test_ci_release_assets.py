import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import call, patch
import zipfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class DevelopmentReleaseAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "ci_release_assets", ROOT / "scripts/upload-ci-release-assets.py"
        )
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.commit = "a" * 40
        self.run = {
            "id": 42, "status": "completed", "conclusion": "success",
            "head_sha": self.commit, "event": "push",
            "head_repository": {"full_name": "owner/project"},
        }
        self.lock = json.loads((ROOT / "sources.lock").read_text())
        self.binary = (
            f"\0Mesa {self.lock['mesaVersion']} "
            f"(git-{self.lock['mesaCommit'][:10]})\0driver"
        ).encode()
        series = json.dumps({"profile": "g615-v11-csf", "variant": "default"}).encode()
        self.files = {
            "libvulkan_panfrost.so": self.binary,
            "series-manifest.json": series,
            "SHA256SUMS.txt": (
                f"{hashlib.sha256(self.binary).hexdigest()}  libvulkan_panfrost.so\n"
            ).encode(),
        }
        self.record = {
            "profile": "g615-v11-csf", "panArch": 11, "frontend": "CSF",
            "abi": "android-aarch64-bionic", "projectCommit": self.commit,
            "githubRunId": "42", "releaseTier": "dev",
            "mesaCommit": self.lock["mesaCommit"], "patchSeriesId": self.lock["patchSeriesId"],
            "binarySha256": hashlib.sha256(self.binary).hexdigest(),
            "seriesManifestSha256": hashlib.sha256(series).hexdigest(),
            "buildId": "1234", "gates": {"build": "PASS", "elf": "PASS"},
        }

    def bundle(self):
        path = self.root / "android.zip"
        with zipfile.ZipFile(path, "w") as archive:
            for name, content in self.files.items():
                archive.writestr(name, content)
            archive.writestr("CI-BUILD.json", json.dumps(self.record))
        return path

    def test_selects_same_commit_non_pr_build_and_rejects_missing_match(self):
        for changes in (
            {"event": "pull_request"}, {"head_sha": "b" * 40},
            {"conclusion": "failure"}, {"status": "in_progress"},
            {"head_repository": {"full_name": "fork/project"}},
        ):
            with self.subTest(changes=changes):
                invalid = {**self.run, **changes}
                self.assertEqual(
                    self.module.select_run([invalid, self.run], "owner/project", self.commit),
                    self.run,
                )
                with self.assertRaisesRegex(ValueError, "successful"):
                    self.module.select_run([invalid], "owner/project", self.commit)

    def test_both_exact_artifacts_must_exist_and_not_be_expired(self):
        artifacts = [
            {"id": number, "name": f"g615-dev-{abi}-{self.commit}", "expired": False}
            for number, abi in enumerate(("android", "glibc"), 1)
        ]
        self.assertEqual(set(self.module.select_artifacts(artifacts, self.commit)),
                         {"android", "glibc"})
        for invalid in (artifacts[:1], [artifacts[0], {**artifacts[1], "expired": True}]):
            with self.subTest(artifacts=invalid), self.assertRaises(ValueError):
                self.module.select_artifacts(invalid, self.commit)

    def test_waits_for_same_commit_build_then_returns_success(self):
        queued = {**self.run, "status": "queued", "conclusion": None}
        running = {**self.run, "status": "in_progress", "conclusion": None}
        pages = [[{"workflow_runs": [run]}] for run in (queued, running, self.run)]
        with patch.object(self.module, "api", side_effect=pages) as api, \
                patch.object(self.module.time, "sleep") as sleep, \
                patch.object(self.module.time, "monotonic", side_effect=[0, 0, 30]):
            result = self.module.wait_for_run("owner/project", self.commit)
        self.assertEqual(result, self.run)
        self.assertEqual(sleep.call_args_list, [call(30), call(30)])
        self.assertTrue(all("status=success" not in call.args[0] for call in api.call_args_list))

    def test_wait_fails_promptly_for_failed_missing_or_unrelated_build(self):
        for runs in (
            [], [{**self.run, "conclusion": "failure"}],
            [{**self.run, "status": "in_progress", "event": "pull_request"}],
            [{**self.run, "status": "queued", "head_sha": "b" * 40}],
        ):
            with self.subTest(runs=runs), \
                    patch.object(self.module, "api", return_value=[{"workflow_runs": runs}]), \
                    patch.object(self.module.time, "sleep") as sleep:
                with self.assertRaisesRegex(ValueError, "successful"):
                    self.module.wait_for_run("owner/project", self.commit)
                sleep.assert_not_called()

    def test_wait_timeout_is_bounded_without_an_extra_sleep(self):
        running = {**self.run, "status": "in_progress", "conclusion": None}
        with patch.object(self.module, "api", return_value=[{"workflow_runs": [running]}]), \
                patch.object(self.module.time, "monotonic", side_effect=[0, 5399, 5400]), \
                patch.object(self.module.time, "sleep") as sleep:
            with self.assertRaisesRegex(ValueError, "timed out"):
                self.module.wait_for_run("owner/project", self.commit)
        sleep.assert_called_once_with(1)

    def test_valid_bundle_keeps_binary_bytes_and_rejects_wrong_provenance(self):
        with patch.object(self.module, "binary_build_id", return_value="1234"):
            self.assertEqual(
                self.module.validate_bundle(self.bundle(), "android", self.commit, 42, self.lock),
                self.binary,
            )
            for changes in (
                {"projectCommit": "b" * 40}, {"githubRunId": "43"},
                {"abi": "linux-aarch64-glibc"}, {"releaseTier": "stable"},
                {"binarySha256": "wrong"}, {"seriesManifestSha256": "wrong"},
                {"buildId": "wrong"}, {"gates": {"build": "PASS", "elf": "FAIL"}},
            ):
                with self.subTest(changes=changes):
                    original = self.record
                    self.record = {**original, **changes}
                    with self.assertRaises(ValueError):
                        self.module.validate_bundle(
                            self.bundle(), "android", self.commit, 42, self.lock
                        )
                    self.record = original

    def test_changed_payload_checksum_and_unsafe_zip_members_are_rejected(self):
        for name, content in (
            ("libvulkan_panfrost.so", b"changed"),
            ("SHA256SUMS.txt", b"wrong checksum"),
            ("../outside", b"untrusted"),
        ):
            with self.subTest(name=name):
                original = dict(self.files)
                self.files[name] = content
                with patch.object(self.module, "binary_build_id", return_value="1234"):
                    with self.assertRaises(ValueError):
                        self.module.validate_bundle(
                            self.bundle(), "android", self.commit, 42, self.lock
                        )
                self.files = original

    def publish(self, existing=(), invalid_glibc=False, moved_tag=False):
        artifacts = [
            {"id": number, "name": f"g615-dev-{abi}-{self.commit}", "expired": False}
            for number, abi in enumerate(("android", "glibc"), 1)
        ]
        commit_queries = 0

        def api(endpoint, paginate=False):
            nonlocal commit_queries
            if "/releases/tags/" in endpoint:
                return {"id": 8, "draft": False}
            if "/commits/" in endpoint:
                commit_queries += 1
                return {"sha": "b" * 40 if moved_tag and commit_queries > 1 else self.commit}
            if "/workflows/" in endpoint:
                return [{"workflow_runs": [self.run]}]
            if "/actions/runs/" in endpoint:
                return [{"artifacts": artifacts}]
            if "/contents/" in endpoint:
                return {"content": base64.b64encode(json.dumps(self.lock).encode()).decode()}
            if "/releases/8/assets" in endpoint:
                return [[{"name": name} for name in existing]]
            self.fail(f"unexpected API call: {endpoint}")

        def download(repository, artifact, path):
            files = dict(self.files)
            record = dict(self.record)
            if "glibc" in artifact["name"]:
                record["abi"] = "linux-aarch64-glibc"
                if invalid_glibc:
                    record["githubRunId"] = "wrong"
                files["panfrost_icd.aarch64.json"] = json.dumps({
                    "ICD": {"library_path": "./libvulkan_panfrost.so"}
                }).encode()
            with zipfile.ZipFile(path, "w") as archive:
                for name, content in files.items():
                    archive.writestr(name, content)
                archive.writestr("CI-BUILD.json", json.dumps(record))

        self.uploads = []

        def command(arguments, **kwargs):
            if arguments[:3] == ["gh", "release", "upload"]:
                self.assertNotIn("--clobber", arguments)
                self.uploads.append({Path(path).name: Path(path).read_bytes()
                                     for path in arguments[6:]})

        with patch.object(self.module, "api", side_effect=api), \
                patch.object(self.module, "download_artifact", side_effect=download), \
                patch.object(self.module, "binary_build_id", return_value="1234"), \
                patch.object(self.module.subprocess, "run", side_effect=command):
            self.module.upload_assets("owner/project", "v27.0.0")

    def test_uploads_dev_binaries_bundles_and_exact_checksums_for_any_release(self):
        self.publish()
        self.assertEqual(len(self.uploads), 1)
        assets = self.uploads[0]
        self.assertEqual(len(assets), 5)
        self.assertEqual(sum(name.endswith(".so") for name in assets), 2)
        self.assertEqual(sum(name.endswith(".zip") for name in assets), 2)
        self.assertTrue(all("dev" in name and self.commit in name for name in assets))
        checksum_name = f"g615-dev-{self.commit}-SHA256SUMS.txt"
        checksums = dict((name, digest) for digest, name in (
            line.split("  ") for line in assets[checksum_name].decode().splitlines()
        ))
        self.assertEqual(set(checksums), set(assets) - {checksum_name})
        for name, digest in checksums.items():
            self.assertEqual(digest, hashlib.sha256(assets[name]).hexdigest())

    def test_no_upload_if_second_abi_fails_assets_exist_or_tag_moves(self):
        for options in (
            {"invalid_glibc": True},
            {"existing": (f"g615-dev-android-{self.commit}.zip",)},
            {"moved_tag": True},
        ):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.publish(**options)
            self.assertEqual(self.uploads, [])
