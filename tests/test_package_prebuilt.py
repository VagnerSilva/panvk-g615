import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/package-prebuilt.sh"


class PackagePrebuiltTest(unittest.TestCase):
    def test_glibc_archive_puts_metadata_first_and_preserves_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            scripts = root / "scripts"
            scripts.mkdir()
            for name in ("package-glibc.sh", "driver_identity.py"):
                shutil.copy2(ROOT / "scripts" / name, scripts / name)
            shutil.copy2(ROOT / "sources.lock", root / "sources.lock")
            (root / "profiles").mkdir()
            shutil.copy2(ROOT / "profiles/g615-v11-csf.json",
                         root / "profiles/g615-v11-csf.json")
            # Provenance gates are independent of ZIP entry ordering.
            (scripts / "compute-patch-series-id.py").write_text(
                'print("sha256:test-series")\n'
            )
            (scripts / "generate-release-manifest.py").write_text(
                "import pathlib, sys\n"
                "stage = pathlib.Path(sys.argv[sys.argv.index('--stage') + 1])\n"
                "for name in ('MANIFEST.json', 'SOURCE.json', 'VALIDATION.json'):\n"
                "    (stage / name).write_text('{}\\n')\n"
            )
            validator = scripts / "validate-package.sh"
            validator.write_text("#!/bin/sh\nexit 0\n")
            validator.chmod(0o755)

            dist = root / "dist/glibc-g615-v11-csf"
            dist.mkdir(parents=True)
            lock = json.loads((root / "sources.lock").read_text())
            data = (f"\x00Mesa {lock['mesaVersion']} "
                    f"(git-{lock['mesaCommit'][:10]})\x00test driver").encode()
            (dist / "libvulkan_panfrost.so").write_bytes(data)
            icd = b'{"ICD":{"library_path":"libvulkan_panfrost.so"}}\n'
            (dist / "panfrost_icd.aarch64.json").write_bytes(icd)
            for name in ("series-manifest.json", "runtime-feature-matrix.json"):
                (dist / name).write_text("{}\n")
            (root / "dist/extension-gap.json").write_text("{}\n")

            subprocess.run(
                ["sh", str(scripts / "package-glibc.sh"),
                 "--profile", "g615-v11-csf"],
                check=True, capture_output=True, text=True, timeout=30,
            )
            archives = list((root / "dist").glob("*.zip"))
            self.assertEqual(len(archives), 1)
            with zipfile.ZipFile(archives[0]) as package:
                self.assertEqual(package.namelist(), [
                    "meta.json", "libvulkan_panfrost.so",
                    "panfrost_icd.aarch64.json", "MANIFEST.json",
                    "series-manifest.json", "SHA256SUMS.txt", "SOURCE.json",
                    "VALIDATION.json", "runtime-feature-matrix.json",
                    "extension-gap.json",
                ])
                meta = json.loads(package.read(package.namelist()[0]))
                self.assertEqual(meta["libraryName"], "libvulkan_panfrost.so")
                self.assertEqual(meta["abi"], "linux-aarch64-glibc")
                self.assertEqual(package.read("libvulkan_panfrost.so"), data)
                self.assertEqual(package.read("panfrost_icd.aarch64.json"), icd)
                self.assertEqual(package.read("SHA256SUMS.txt").decode(),
                                 f"{hashlib.sha256(data).hexdigest()}  libvulkan_panfrost.so\n")
                self.assertIsNone(package.testzip())

    def test_archives_keep_canonical_profile_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            so = root / "driver.so"
            so.write_bytes(b"\x00Mesa 27.0.0-devel (git-13baeb70c0)\x00test driver")
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
