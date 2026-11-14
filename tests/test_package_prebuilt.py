import json
import pathlib
import subprocess
import tempfile
import unittest
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/package-prebuilt.sh"


class PackagePrebuiltTest(unittest.TestCase):
    def test_archives_keep_canonical_profile_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            so = root / "driver.so"
            so.write_bytes(b"test driver")
            icd = root / "icd.json"
            icd.write_text('{"ICD":{"library_path":"libvulkan_panfrost.so"}}\n')
            out = root / "out"

            subprocess.run(
                [
                    str(SCRIPT),
                    "--so", str(so),
                    "--icd", str(icd),
                    "--version", "v0.1.0-rc1",
                    "--profile", "g615-v11-csf",
                    "--outdir", str(out),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            archives = list(out.glob("*.zip"))
            self.assertEqual(len(archives), 2)
            for archive in archives:
                with zipfile.ZipFile(archive) as package:
                    self.assertEqual(
                        json.loads(package.read("meta.json"))["profile"],
                        "g615-v11-csf",
                    )
                    self.assertEqual(
                        json.loads(package.read("MANIFEST.json"))["profile"],
                        "g615-v11-csf",
                    )
                    self.assertEqual(
                        json.loads(package.read("VALIDATION.json"))["profile"],
                        "g615-v11-csf",
                    )


if __name__ == "__main__":
    unittest.main()
