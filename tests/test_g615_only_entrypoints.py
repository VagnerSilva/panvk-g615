import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class G615OnlyEntrypointTests(unittest.TestCase):
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
