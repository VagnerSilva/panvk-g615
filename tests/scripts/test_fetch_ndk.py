import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/fetch-ndk.sh"
VERSION = "30.0.16248370"


class FetchNdkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.work = self.root / "work"
        self.env = os.environ.copy()
        self.env["PATH"] = f"{self.bin}:/usr/bin:/bin"
        self.tool("curl", 'while [ "$1" != "--output" ]; do shift; done\n: > "$2"')
        self.tool("sha1sum", "exit 0")
        self.tool(
            "unzip",
            'while [ "$1" != "-d" ]; do shift; done\n'
            'dest="$2/android-ndk-r30"\n'
            'mkdir -p "$dest/toolchains/llvm/prebuilt/linux-x86_64/bin"\n'
            f'echo "Pkg.Revision = {VERSION}" > "$dest/source.properties"\n'
            ': > "$dest/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android29-clang"\n'
            'chmod +x "$dest/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android29-clang"',
        )

    def tool(self, name, body):
        path = self.bin / name
        path.write_text(f"#!/bin/sh\nset -eu\n{body}\n")
        path.chmod(0o755)

    def run_script(self):
        return subprocess.run(
            [str(SCRIPT), "--work", str(self.work)],
            env=self.env,
            text=True,
            capture_output=True,
        )

    def test_install_and_reuse(self):
        first = self.run_script()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertTrue((self.work / "ndk" / VERSION / "source.properties").is_file())
        self.tool("curl", "exit 99")
        second = self.run_script()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("already installed", second.stdout)

    def test_checksum_failure_cleans_stage(self):
        self.tool("sha1sum", "exit 1")
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list((self.work / "ndk").iterdir()), [])

    def test_refuses_existing_destination(self):
        dest = self.work / "ndk" / VERSION
        dest.mkdir(parents=True)
        marker = dest / "keep"
        marker.write_text("unchanged")
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("existing destination", result.stderr)
        self.assertEqual(marker.read_text(), "unchanged")

    def test_refuses_unsupported_host(self):
        self.tool("uname", '[ "$1" = "-s" ] && echo Linux || echo aarch64')
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("x86_64", result.stderr)
        self.assertFalse(self.work.exists())

    def test_rejects_missing_argument(self):
        result = subprocess.run([str(SCRIPT), "--work"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
