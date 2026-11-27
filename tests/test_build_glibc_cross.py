import os
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/build-glibc.sh"


class GlibcCrossBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in ("scripts", "profiles", "meson", "bin"):
            (self.root / directory).mkdir()
        shutil.copy2(SCRIPT, self.root / "scripts/build-glibc.sh")
        (self.root / "profiles/g615-v11-csf.json").write_text("{}")
        (self.root / "sources.lock").write_text('{"mesaCommit":"test-pin"}')
        (self.root / "cross.ini").write_text("[host_machine]\n")
        self.log = self.root / "commands"
        self.env = dict(os.environ, PATH=f"{self.root}/bin:{os.environ['PATH']}",
                        TEST_ROOT=str(self.root), TEST_LOG=str(self.log),
                        ANDROID_SERIAL="ambient-device",
                        PKG_CONFIG_PATH="/wrong-host-path",
                        PANVK_HOST_TOOLS_CACHE="/wrong-cache")
        self.stub("uname", 'echo x86_64')
        self.stub("git", 'echo test-pin')
        self.stub("adb", 'echo "adb $*" >> "$TEST_LOG"; exit 91')
        self.stub("file", 'echo "ELF 64-bit ARM aarch64"')
        self.stub("readelf", 'case "$1" in --version-info) echo GLIBC_2.17;; -s) echo kbase_kmod_ops;; esac')
        self.script("fetch-mesa.sh", 'mkdir "$1/mesa"')
        self.script("apply-patches.sh", '''
while [ "$#" -gt 0 ]; do
  if [ "$1" = --series-manifest ]; then printf '{}\\n' > "$2"; break; fi
  shift
done
''')
        self.script("bootstrap-host-tools.sh", '''
printf 'bootstrap cache=%s %s\\n' "${PANVK_HOST_TOOLS_CACHE-unset}" "$*" >> "$TEST_LOG"
while [ "$#" -gt 0 ]; do
  if [ "$1" = --out ]; then mkdir -p "$2/bin"; break; fi
  shift
done
''')
        self.stub("meson", '''
printf 'meson pkg=%s %s\\n' "${PKG_CONFIG_PATH-unset}" "$*" >> "$TEST_LOG"
[ "${FAIL_MESON:-0}" = 0 ] || exit 47
mkdir -p "$2/src/panfrost/vulkan"
touch "$2/build.ninja"
''')
        self.stub("ninja", '''
printf 'ninja %s\\n' "$*" >> "$TEST_LOG"
while [ "$#" -gt 0 ]; do
  if [ "$1" = -C ]; then dir="$2"; break; fi
  shift
done
touch "$dir/src/panfrost/vulkan/libvulkan_panfrost.so"
echo '{"ICD":{"api_version":"1.4","library_path":"/usr/local/lib/libvulkan_panfrost.so"}}' > "$dir/src/panfrost/vulkan/panfrost_icd.aarch64.json"
''')

    def stub(self, name, body):
        path = self.root / "bin" / name
        path.write_text("#!/bin/sh\nset -eu\n" + body + "\n")
        path.chmod(0o755)

    def script(self, name, body):
        path = self.root / "scripts" / name
        path.write_text("#!/bin/sh\nset -eu\n" + body + "\n")
        path.chmod(0o755)

    def run_build(self, *args):
        return subprocess.run(
            ["sh", str(self.root / "scripts/build-glibc.sh"),
             "--profile", "g615-v11-csf", *args],
            env=self.env, text=True, capture_output=True)

    def test_cross_build_is_local_isolated_and_headless_only_when_requested(self):
        result = self.run_build("--cross-file", str(self.root / "cross.ini"),
                                "--headless", "--with-kbase-sync")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.log.read_text()
        self.assertNotIn("adb ", calls)
        self.assertIn("bootstrap cache=unset", calls)
        self.assertIn("meson pkg=unset", calls)
        self.assertIn("--cross-file " + str(self.root / "cross.ini"), calls)
        self.assertIn("-Dplatforms=", calls)
        self.assertIn("-Dmesa-clc=system", calls)
        self.assertIn("-Dprecomp-compiler=system", calls)
        outputs = list((self.root / "dist").glob(
            "glibc-g615-v11-csf-kbase-sync-002-004-*/libvulkan_panfrost.so"))
        self.assertEqual(len(outputs), 1)
        manifest = json.loads((outputs[0].parent / "panfrost_icd.aarch64.json").read_text())
        self.assertEqual(manifest["ICD"]["library_path"], "./libvulkan_panfrost.so")
        self.assertEqual(manifest["ICD"]["api_version"], "1.4")

    def test_cross_build_keeps_wsi_by_default(self):
        result = self.run_build("--cross-file", str(self.root / "cross.ini"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("-Dplatforms=x11,wayland", self.log.read_text())

    def test_invalid_or_conflicting_cross_options_fail_before_fetch(self):
        for args in (("--cross-file", str(self.root / "missing")), ("--headless",),
                     ("--cross-file", str(self.root / "cross.ini"),
                      "--serial", "device"),
                     ("--cross-file", str(self.root / "cross.ini"),
                      "--device-root", "/tmp/device"),
                     ("--cross-file", str(self.root / "cross.ini"),
                      "--chroot-wrapper", "/tmp/wrapper")):
            with self.subTest(args=args):
                result = self.run_build(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.root / "build").exists())

    def test_cross_configuration_failure_is_not_published(self):
        self.env["FAIL_MESON"] = "1"
        result = self.run_build("--cross-file", str(self.root / "cross.ini"))
        self.assertEqual(result.returncode, 47)
        self.assertFalse((self.root / "dist").exists())

    def test_device_dispatch_remains_available(self):
        result = self.run_build("--serial", "device")
        self.assertEqual(result.returncode, 91)
        self.assertIn("adb -s device shell", self.log.read_text())

    def test_native_aarch64_keeps_native_file(self):
        self.stub("uname", "echo aarch64")
        result = self.run_build()
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.log.read_text()
        self.assertIn("--native-file", calls)
        self.assertIn("-Dplatforms=x11,wayland", calls)
        self.assertNotIn("adb ", calls)
        self.assertNotIn("bootstrap", calls)


if __name__ == "__main__":
    unittest.main()
