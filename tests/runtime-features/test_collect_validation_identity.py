import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "collector", ROOT / "scripts" / "collect-validation.py"
)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)

CURRENT = "7" * 64
OTHER = "5" * 64


class EvidenceIdentity(unittest.TestCase):
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
