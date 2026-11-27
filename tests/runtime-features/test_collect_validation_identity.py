import importlib.util
import pathlib
import tempfile
import unittest
import hashlib
import json
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "collector", ROOT / "scripts" / "collect-validation.py"
)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
from build_provenance import series_manifest

CURRENT = "7" * 64
OTHER = "5" * 64


class EvidenceIdentity(unittest.TestCase):
    def test_staged_candidate_and_abi_override_historical_dist_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            stage = pathlib.Path(temp)
            binary = stage / "libvulkan_panfrost.so"
            binary.write_bytes(b"staged-candidate")
            sha = hashlib.sha256(binary.read_bytes()).hexdigest()
            manifest = series_manifest(ROOT, "g615-v11-csf", "kbase-sync-002-004")
            (stage / "series-manifest.json").write_text(json.dumps(manifest))
            def candidate_hash(path):
                return sha if path == binary else OTHER

            def candidate_evidence(vdir, gate, patterns, tokens, binary_sha):
                return {"status": "pass" if binary_sha == sha else "untested",
                        "binarySha256": binary_sha}

            for abi, section in (("android-aarch64-bionic", "android"),
                                 ("linux-aarch64-glibc", "glibc")):
                with self.subTest(abi=abi), \
                     mock.patch.object(collector, "sha256_file", side_effect=candidate_hash), \
                     mock.patch.object(collector, "evidence", side_effect=candidate_evidence):
                    doc = collector.collect("g615-v11-csf", stage, abi)
                self.assertEqual(doc["binarySha256"], sha)
                self.assertEqual(doc["variant"], "kbase-sync-002-004")
                self.assertTrue(all(gate["binarySha256"] == sha
                                    for gate in doc[section].values()))
                self.assertEqual(collector.require_beta_gates(doc, abi), [])
                self.assertTrue(collector.require_beta_gates(doc))

    def check_log(self, text, binary=CURRENT):
        with tempfile.TemporaryDirectory() as temp:
            directory = pathlib.Path(temp)
            (directory / "gate.txt").write_text(text)
            return collector.evidence(
                directory, "compute10", ["gate.txt"], ("D+E-PASS",), binary
            )

    def test_accepts_matching_driver_hash(self):
        result = self.check_log(f"DRIVER_SHA256={CURRENT}\nD+E-PASS\n")
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["binarySha256"], CURRENT)

    def test_accepts_matching_sha256sum(self):
        result = self.check_log(f"{CURRENT}  /tmp/libvulkan_panfrost.so\nD+E-PASS\n")
        self.assertEqual(result["status"], "pass")

    def test_rejects_old_binary(self):
        result = self.check_log(f"{OTHER}  /tmp/libvulkan_panfrost.so\nD+E-PASS\n")
        self.assertEqual(result["status"], "untested")

    def test_rejects_unidentified_evidence(self):
        self.assertEqual(self.check_log("D+E-PASS\n")["status"], "untested")

    def test_rejects_unidentified_candidate(self):
        result = self.check_log(f"DRIVER_SHA256={CURRENT}\nD+E-PASS\n", None)
        self.assertEqual(result["status"], "untested")

    def test_rejects_conflicting_identifiers(self):
        text = f"DRIVER_SHA256={CURRENT}\n{OTHER}  /tmp/libvulkan_panfrost.so\nD+E-PASS\n"
        self.assertEqual(self.check_log(text)["status"], "untested")


if __name__ == "__main__":
    unittest.main()
