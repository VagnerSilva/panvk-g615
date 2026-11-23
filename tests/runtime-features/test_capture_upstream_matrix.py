import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import runpy

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "capture-matrix.py"


class CaptureUpstreamMatrix(unittest.TestCase):
    def test_extracts_vulkan_driver_rows_and_revision(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            mesa = root / "mesa"
            (mesa / "docs").mkdir(parents=True)
            (mesa / "VERSION").write_text("27.0.0-devel\n")
            (mesa / "docs" / "features.txt").write_text(
                "Vulkan 1.1 -- all DONE: panvk\n"
                "  VK_KHR_16bit_storage DONE (anv, panvk/v10+)\n"
                "  VK_EXT_other DONE (anv)\n"
                "  VK_EXT_future not started\n"
            )
            out = root / "out"
            args = [str(SCRIPT), "--mesa", str(mesa), "--out", str(out)]
            with mock.patch.object(sys, "argv", args), mock.patch.object(
                subprocess, "check_output", return_value="1" * 40 + "\n"
            ):
                runpy.run_path(str(SCRIPT), run_name="__main__")
            matrix = json.loads((out / "upstream-feature-matrix.json").read_text())
            self.assertEqual(matrix["mesaCommit"], "1" * 40)
            self.assertEqual(matrix["mesaVersion"], "27.0.0-devel")
            self.assertEqual(matrix["panvk"]["done"], 1)
            rows = {r["name"]: r for r in matrix["rows"]}
            self.assertIn("panvk/v10+", rows["VK_KHR_16bit_storage"]["drivers"])
            self.assertNotIn("panvk", rows["VK_EXT_other"]["drivers"])

    def test_missing_features_file_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "--mesa", str(root), "--out", str(root / "out")],
                text=True, capture_output=True,
            )
            self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
