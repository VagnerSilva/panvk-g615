import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_provenance import series_manifest


class BuildRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("ci_record", ROOT / "scripts/record-ci-build.py")
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_record_identifies_binary_inputs_and_toolchain_without_runtime_claims(self):
        lock = json.loads((ROOT / "sources.lock").read_text())
        binary = f"\0Mesa {lock['mesaVersion']} (git-{lock['mesaCommit'][:10]})\0fixture".encode()
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "libvulkan_panfrost.so").write_bytes(binary)
            manifest = (json.dumps(series_manifest(ROOT, "g615-v11-csf", "default")) + "\n").encode()
            (stage / "series-manifest.json").write_bytes(manifest)
            ndk = stage / "ndk"
            ndk.mkdir()
            (ndk / "source.properties").write_text("Pkg.Revision = 30.0.16248370\n")

            def command(*args):
                if args[0] == "python3":
                    return lock["patchSeriesId"]
                return " ".join(args)

            with patch.object(self.module, "command", side_effect=command), \
                    patch.object(self.module, "binary_build_id", return_value="fixture-id"), \
                    patch.dict(os.environ, {
                        "GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "1",
                        "ANDROID_NDK_ROOT": str(ndk), "ANDROID_API": "35",
                    }), patch.object(sys, "argv", [
                        "record-ci-build.py", "--abi", "android", "--stage", str(stage),
                    ]):
                self.module.main()
            data = json.loads((stage / "CI-BUILD.json").read_text())
            self.assertEqual(data["binarySha256"], hashlib.sha256(binary).hexdigest())
            self.assertEqual(data["seriesManifestSha256"], hashlib.sha256(manifest).hexdigest())
            self.assertEqual(data["androidApi"], 35)
            self.assertEqual(data["githubRunId"], "123")
            self.assertIn("android35-clang", data["toolchain"]["compiler"])
            for gate in ("runtime", "stability", "performance"):
                self.assertEqual(data["gates"][gate], "NOT EXECUTED")
            self.assertEqual(
                (stage / "SHA256SUMS.txt").read_text(),
                f"{hashlib.sha256(binary).hexdigest()}  libvulkan_panfrost.so\n",
            )


if __name__ == "__main__":
    unittest.main()
