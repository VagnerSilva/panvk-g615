import hashlib
import json
import pathlib
import subprocess
import tempfile
import unittest
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/package-launcher-zips.sh"
SO = b"\x00Mesa 27.0.0-devel (git-13baeb70c0)\x00test driver"


class PackageLauncherZipsTest(unittest.TestCase):
    def test_ci_packages_include_both_abis_metadata_and_recorded_android_api(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            stages = {}
            records = {}
            driver_info = "PanVK-kbase recorded-driver (Mesa 27.0.0-devel (git-13baeb70c0))"
            payloads = {abi: b"\0" + driver_info.encode() + b"\0" + abi.encode()
                        for abi in ("android", "glibc")}
            lock = json.loads((ROOT / "sources.lock").read_text())
            for abi, payload in payloads.items():
                stage = root / abi
                stage.mkdir()
                series = b'{"profile":"g615-v11-csf","variant":"default"}\n'
                record = {
                    "profile": "g615-v11-csf", "projectCommit": "a" * 40,
                    "abi": "android-aarch64-bionic" if abi == "android" else "linux-aarch64-glibc",
                    "releaseTier": "dev", "androidApi": 35 if abi == "android" else None,
                    "mesaCommit": lock["mesaCommit"], "patchSeriesId": lock["patchSeriesId"],
                    "binarySha256": hashlib.sha256(payload).hexdigest(),
                    "seriesManifestSha256": hashlib.sha256(series).hexdigest(),
                    "gates": {"build": "PASS", "elf": "PASS", "runtime": "NOT EXECUTED"},
                }
                (stage / "libvulkan_panfrost.so").write_bytes(payload)
                (stage / "series-manifest.json").write_bytes(series)
                (stage / "CI-BUILD.json").write_text(json.dumps(record))
                if abi == "glibc":
                    (stage / "panfrost_icd.aarch64.json").write_text(
                        '{"ICD":{"library_path":"./libvulkan_panfrost.so","api_version":"1.4.363"}}'
                    )
                stages[abi] = stage
                records[abi] = record
            command = [
                str(SCRIPT), "--so", str(stages["android"] / "libvulkan_panfrost.so"),
                "--ci-android-stage", str(stages["android"]),
                "--ci-glibc-stage", str(stages["glibc"]),
                "--source-lock", str(ROOT / "sources.lock"), "--outdir", str(root / "output"),
                "--version", "v1.0.0-dev",
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            archives = list((root / "output").glob("*.zip"))
            self.assertEqual(len(archives), 8)
            self.assertEqual(sum(p.name.endswith(".adpkg.zip") for p in archives), 1)
            self.assertEqual(sum(p.name.endswith("-EMULATOR.zip") for p in archives), 1)
            stem = "Pankv-G615-v1.0.0"
            self.assertEqual({p.name for p in archives}, {
                f"{stem}-{launcher}.zip" for launcher in (
                    "adrenotools", "winlator", "bannerlator", "cmod", "ludashi", "gamehub"
                )
            } | {f"{stem}.adpkg.zip", "Pankv-G615-v1.0.0-EMULATOR.zip"})
            for path in archives:
                abi = "glibc" if path.name.endswith("-EMULATOR.zip") else "android"
                with zipfile.ZipFile(path) as archive:
                    self.assertEqual(archive.namelist()[0], "meta.json")
                    self.assertTrue(all("/" not in name for name in archive.namelist()))
                    meta = json.loads(archive.read("meta.json"))
                    library = "libvulkan_freedreno.so" if path.name.endswith("-gamehub.zip") \
                        else "libvulkan_panfrost.so"
                    self.assertEqual(meta["libraryName"], library)
                    self.assertEqual(meta["driverVersion"], driver_info)
                    self.assertEqual(meta["packageVersion"], "1.0.0-dev")
                    self.assertEqual(meta["abi"], records[abi]["abi"])
                    self.assertEqual(archive.read(library), payloads[abi])
                    self.assertEqual(json.loads(archive.read("CI-BUILD.json")), records[abi])
                    self.assertEqual(archive.read("series-manifest.json"),
                                     (stages[abi] / "series-manifest.json").read_bytes())
                    self.assertEqual(archive.read("SHA256SUMS.txt").decode(),
                                     f"{records[abi]['binarySha256']}  {library}\n")
                    if abi == "android":
                        self.assertEqual(meta["minApi"], 35)
                    else:
                        self.assertNotIn("minApi", meta)
                        self.assertEqual(json.loads(archive.read("panfrost_icd.aarch64.json"))
                                         ["ICD"]["library_path"], "./libvulkan_panfrost.so")
                    if path.name.endswith("-bannerlator.zip"):
                        self.assertIn(meta["name"],
                                      archive.read("panvk_icd_abs.aarch64.json").decode())
                        self.assertIn(driver_info, archive.read("README-bannerlator.txt").decode())
                    self.assertIsNone(archive.testzip())
            (stages["android"] / "libvulkan_panfrost.so").write_bytes(b"changed")
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("binary", result.stderr)

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
            self.assertEqual([p.name for p in archives], ["Pankv-G615-v0.0.0.adpkg.zip"])
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
            stem = "Pankv-G615-v0.0.0"
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

    def test_development_adpkg_uses_legacy_driver_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            so = root / "driver.so"
            info = "PanVK-kbase dev (Mesa 27.0.0-devel (git-13baeb70c0))"
            so.write_bytes(b"\x00" + info.encode() + b"\x00")
            out = root / "output"
            subprocess.run(
                [str(SCRIPT), "--so", str(so), "--outdir", str(out),
                 "--only", "adpkg", "--dev-name", "PanVK-Mesa27-G615-dev"],
                check=True, capture_output=True, text=True,
            )
            with zipfile.ZipFile(next(out.iterdir())) as package:
                self.assertEqual(json.loads(package.read("meta.json"))["driverVersion"],
                                 info)

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

    def test_missing_or_stale_driver_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            so = root / "driver.so"
            for data, message in (
                (b"no driverInfo", "missing driver identity"),
                (b"\x00Mesa 26.3.0-devel (git-13baeb70c0)\x00", "pinned Mesa revision"),
                (b"\x00Mesa 27.0.0-devel (git-abcdef1234)\x00", "pinned Mesa revision"),
            ):
                so.write_bytes(data)
                result = subprocess.run(
                    [str(SCRIPT), "--so", str(so), "--outdir", str(root / "out")],
                    text=True, capture_output=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertEqual(list((root / "out").glob("*.zip")), [])


if __name__ == "__main__":
    unittest.main()
