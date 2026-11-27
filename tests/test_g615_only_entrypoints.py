import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class G615OnlyEntrypointTests(unittest.TestCase):
    def test_android_ndk_default_and_explicit_overrides(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "scripts").mkdir()
            env = dict(os.environ, ANDROID_HOME=str(root / "unused-sdk"))
            env.pop("ANDROID_NDK_ROOT", None)
            for name in ("build-android.sh", "build-android-deps.sh"):
                shutil.copy2(ROOT / "scripts" / name, root / "scripts" / name)
                args = ["sh", str(root / "scripts" / name)]
                if name == "build-android.sh":
                    args += ["--profile", "g615-v11-csf"]
                for selection, extra_env, extra_args, expected in (
                    ("default", {}, [], root / "work/ndk/30.0.16248370"),
                    ("environment", {"ANDROID_NDK_ROOT": str(root / "env-ndk")},
                     [], root / "env-ndk"),
                    ("argument", {"ANDROID_NDK_ROOT": str(root / "env-ndk")},
                     ["--ndk", str(root / "arg-ndk")], root / "arg-ndk"),
                ):
                    with self.subTest(script=name, selection=selection):
                        result = subprocess.run(
                            args + extra_args, text=True, capture_output=True,
                            env={**env, **extra_env}, timeout=10,
                        )
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn(
                            f"NDK toolchain not found under {expected}", result.stderr
                        )
                        self.assertFalse((root / "build").exists())
                        self.assertFalse((root / "work").exists())

    def test_only_g615_profile_and_no_legacy_build_entrypoints(self):
        self.assertEqual(
            sorted(path.stem for path in (ROOT / "profiles").glob("*.json")),
            ["g615-v11-csf"],
        )
        for name in ("prepare-rc5-tree.sh", "build-v9-test-driver.sh"):
            self.assertFalse((ROOT / "scripts" / name).exists(), name)

    def test_other_profiles_fail_before_packaging_or_release_changes(self):
        commands = (
            ("sh", "scripts/release-local.sh"),
            ("sh", "scripts/build-all.sh"),
            ("sh", "scripts/package-android-adpkg.sh"),
            ("sh", "scripts/package-glibc.sh"),
            ("sh", "scripts/package-prebuilt.sh"),
            ("python3", "scripts/generate-release-manifest.py"),
            ("python3", "scripts/compute-patch-series-id.py"),
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "scripts").mkdir()
            for interpreter, name in commands:
                shutil.copy2(ROOT / name, root / name)
                args = [interpreter, str(root / name), "--profile", "g52-v7-jm"]
                if name.endswith("generate-release-manifest.py"):
                    args += ["--abi", "android-aarch64-bionic", "--stage", str(root / "stage")]
                with self.subTest(script=name):
                    result = subprocess.run(args, text=True, capture_output=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("only g615-v11-csf is supported", result.stderr)
                    self.assertFalse((root / "dist").exists())
                    self.assertFalse((root / "stage").exists())
                    self.assertFalse((root / "work").exists())

    def test_other_profiles_fail_before_mesa_or_build_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "scripts").mkdir()
            (root / "profiles").mkdir()
            (root / "mesa").mkdir()
            for name in ("apply-patches.sh", "build-android.sh", "build-glibc.sh"):
                shutil.copy2(ROOT / "scripts" / name, root / "scripts" / name)
            for profile, arch, frontend in (
                ("g610-v10-csf", 10, "CSF"),
                ("g52-v7-jm", 7, "JM"),
            ):
                (root / "profiles" / f"{profile}.json").write_text(
                    json.dumps({"panArch": arch, "frontend": frontend})
                )
            env = dict(os.environ, ANDROID_NDK_ROOT=str(root / "missing-ndk"))
            for name in ("apply-patches.sh", "build-android.sh", "build-glibc.sh"):
                for profile in ("g610-v10-csf", "g52-v7-jm"):
                    with self.subTest(script=name, profile=profile):
                        args = ["sh", str(root / "scripts" / name), "--profile", profile]
                        if name == "apply-patches.sh":
                            args += ["--mesa", str(root / "mesa")]
                        result = subprocess.run(args, text=True, capture_output=True, env=env)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn("only g615-v11-csf is supported", result.stderr)
                        self.assertFalse((root / "build").exists())
                        self.assertEqual(list((root / "mesa").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
