import hashlib
import json
import pathlib
import subprocess
import tempfile
import unittest
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/package-launcher-zips.sh"
SO = b"\x00Mesa 26.3.0-devel (git-abcdef1234)\x00test driver"


class PackageLauncherZipsTest(unittest.TestCase):
    def test_only_adpkg_contains_driver_and_no_device_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            so = root / "driver.so"
            so.write_bytes(SO)
            out = root / "output"
            subprocess.run(
                [str(SCRIPT), "--so", str(so), "--outdir", str(out), "--only", "adpkg"],
                check=True,
                capture_output=True,
                text=True,
            )
            archives = list(out.iterdir())
            self.assertEqual([p.name for p in archives], ["Mesa-PanVK-Android-v0.0.0-dev-abcdef12.adpkg.zip"])
            with zipfile.ZipFile(archives[0]) as package:
                self.assertEqual(set(package.namelist()), {
                    "libvulkan_panfrost.so", "meta.json", "SHA256SUMS.txt", "VALIDATION.json"
                })
                first_json = next(name for name in package.namelist()
                                  if ".json" in name.lower())
                self.assertEqual(first_json, "meta.json")
                self.assertEqual(package.read("libvulkan_panfrost.so"), SO)
                meta = json.loads(package.read(first_json))
                for field in ("name", "description", "author", "vendor",
                              "driverVersion", "libraryName"):
                    self.assertIsInstance(meta[field], str)
                    self.assertTrue(meta[field])
                self.assertEqual(meta["libraryName"], "libvulkan_panfrost.so")
                self.assertIsInstance(meta["minApi"], int)
                self.assertEqual(meta["minApi"], 35)
                validation = json.loads(package.read("VALIDATION.json"))
                self.assertEqual(validation["status"], "not-revalidated-by-packaging")
                self.assertEqual(validation["binarySha256"], hashlib.sha256(SO).hexdigest())

    def test_default_preserves_launcher_outputs_and_adds_adpkg(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            so = root / "driver.so"
            so.write_bytes(SO)
            out = root / "output"
            subprocess.run([str(SCRIPT), "--so", str(so), "--outdir", str(out)],
                           check=True, capture_output=True, text=True)
            names = {p.name for p in out.iterdir()}
            stem = "Mesa-PanVK-Android-v0.0.0-dev-abcdef12"
            self.assertEqual(names, {f"{stem}-{name}.zip" for name in (
                "adrenotools", "winlator", "bannerlator", "cmod", "ludashi", "gamehub"
            )} | {f"{stem}.adpkg.zip"})
            for archive in out.iterdir():
                with zipfile.ZipFile(archive) as package:
                    first_json = next(name for name in package.namelist()
                                      if ".json" in name.lower())
                    self.assertEqual(first_json, "meta.json", archive.name)

    def test_release_version_cannot_use_dev_adpkg(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            so = root / "driver.so"
            so.write_bytes(SO)
            result = subprocess.run(
                [str(SCRIPT), "--so", str(so), "--outdir", str(root / "output"),
                 "--version", "v0.1.0-rc4", "--only", "adpkg"],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("require a -dev version", result.stderr)

    def test_explicit_development_name_and_invalid_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            so = root / "driver.so"
            so.write_bytes(SO)
            out = root / "output"
            command = [str(SCRIPT), "--so", str(so), "--outdir", str(out),
                       "--only", "adpkg", "--dev-name"]
            subprocess.run(command + ["PanVK-G615-exp-871ca629"], check=True,
                           capture_output=True, text=True)
            with zipfile.ZipFile(next(out.iterdir())) as package:
                self.assertEqual(json.loads(package.read("meta.json"))["name"],
                                 "PanVK-G615-exp-871ca629")
                self.assertEqual(package.read("libvulkan_panfrost.so"), SO)
            for name in ("../driver", "bad name", "é", "x" * 129):
                result = subprocess.run(command + [name], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("invalid --dev-name", result.stderr)
            for value in ([], [""]):
                result = subprocess.run(command + value, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("--dev-name requires a name", result.stderr)

    def test_development_name_requires_only_adpkg(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            so = root / "driver.so"
            so.write_bytes(SO)
            result = subprocess.run(
                [str(SCRIPT), "--so", str(so), "--outdir", str(root / "output"),
                 "--dev-name", "PanVK-test"],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--dev-name requires --only adpkg", result.stderr)


if __name__ == "__main__":
    unittest.main()
