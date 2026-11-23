#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PIN = json.loads((ROOT / "sources.lock").read_text())["mesaCommit"]
FIXTURES = ROOT / "build" / ("g615-series-tests-" + str(os.getpid()))


class SeriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        FIXTURES.mkdir(parents=True)
        cls.bin = FIXTURES / "bin"
        cls.bin.mkdir()
        git = cls.bin / "git"
        git.write_text("""#!/bin/sh
case " $* " in
  *" rev-parse HEAD "*) echo "$TEST_PIN";;
  *" status "*) [ "${DIRTY:-0}" = 0 ] || echo '?? previous-output';;
  *" apply "*"--check"*) [ "${FAIL_PATCH:-0}" = 0 ];;
  *" apply "*) [ "${FAIL_PATCH:-0}" = 0 ];;
esac
""")
        git.chmod(0o755)
        cls.env = dict(os.environ, PATH=f"{cls.bin}:{os.environ['PATH']}", TEST_PIN=PIN)

    def replay(self, name, *args, env=None):
        mesa = FIXTURES / (name + "-mesa")
        mesa.mkdir()
        manifest = FIXTURES / (name + ".json")
        result = subprocess.run(
            ["sh", str(ROOT / "scripts/apply-patches.sh"), "--profile", "g615-v11-csf",
             "--mesa", str(mesa), "--series-manifest", str(manifest), *args],
            env=env or self.env, text=True, capture_output=True)
        return result, manifest

    def test_sync_selection(self):
        default, default_manifest = self.replay("default")
        sync, sync_manifest = self.replay("sync", "--with-kbase-sync")
        self.assertEqual(default.returncode, 0, default.stderr)
        self.assertEqual(sync.returncode, 0, sync.stderr)
        a = json.loads(default_manifest.read_text())
        b = json.loads(sync_manifest.read_text())
        patches = [x["path"] for x in b["inputs"] if x["path"].endswith(".patch")]
        ids = [Path(p).name[:3] for p in patches]
        self.assertEqual(ids[-3:], ["002", "003", "004"])
        self.assertFalse(any("experimental-kbase-sync" in x["path"] for x in a["inputs"]))
        self.assertFalse(any("/experimental-kbase-sync/001" in p for p in patches))
        self.assertEqual((a["variant"], b["variant"]), ("default", "kbase-sync-002-004"))
        for item in b["inputs"]:
            self.assertEqual(item["sha256"], hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest())
        self.assertTrue(any("/files/" in x["path"] for x in b["inputs"]))

    def test_variant_isolates_build(self):
        a, pa = self.replay("id-default")
        b, pb = self.replay("id-sync", "--with-kbase-sync")
        self.assertEqual((a.returncode, b.returncode), (0, 0), a.stderr + b.stderr)
        self.assertNotEqual(hashlib.sha256(pa.read_bytes()).hexdigest(),
                            hashlib.sha256(pb.read_bytes()).hexdigest())
        script = (ROOT / "scripts/build-glibc.sh").read_text()
        self.assertIn("--with-kbase-sync", script)
        self.assertIn("--series-manifest", script)

    def test_failure_does_not_publish_manifest(self):
        result, manifest = self.replay("failed", env=dict(self.env, FAIL_PATCH="1"))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(manifest.exists())

    def test_manifest_destination_and_checkout_rejected(self):
        result, manifest = self.replay("wrong-pin", env=dict(self.env, TEST_PIN="wrong"))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(manifest.exists())
        result, manifest = self.replay("dirty", env=dict(self.env, DIRTY="1"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("working tree must be clean", result.stderr)
        self.assertFalse(manifest.exists())
        mesa = FIXTURES / "existing-mesa"
        mesa.mkdir()
        destination = FIXTURES / "existing.json"
        destination.write_text("preserve")
        result = subprocess.run(
            ["sh", str(ROOT / "scripts/apply-patches.sh"), "--profile", "g615-v11-csf",
             "--mesa", str(mesa), "--series-manifest", str(destination)],
            env=self.env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid manifest destination", result.stderr)
        self.assertEqual(destination.read_text(), "preserve")

    def test_device_build_publishes_separately_and_only_on_success(self):
        project = FIXTURES / "project"
        for directory in ("scripts", "profiles", "bin"):
            (project / directory).mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / "scripts/build-glibc.sh", project / "scripts")
        shutil.copy(ROOT / "sources.lock", project)
        shutil.copy(ROOT / "profiles/g615-v11-csf.json", project / "profiles")
        commands = {
            "scripts/fetch-mesa.sh": '#!/bin/sh\nmkdir "$1/mesa"\n',
            "scripts/apply-patches.sh": """#!/bin/sh
variant=default
while [ $# -gt 0 ]; do
 case "$1" in
 --series-manifest) manifest="$2"; shift 2;;
 --with-kbase-sync) variant=kbase-sync-002-004; shift;;
 *) shift;;
 esac
done
printf '{"variant":"%s"}\\n' "$variant" > "$manifest"
""",
            "bin/uname": '#!/bin/sh\necho x86_64\n',
            "bin/git": '#!/bin/sh\necho "$TEST_PIN"\n',
            "bin/adb": """#!/bin/sh
printf '%s\\n' "$*" >> "$ADB_LOG"
case "$*" in
 *" pull "*"panfrost_icd"*) [ "${FAIL_PULL:-0}" = 0 ] || exit 1; echo '{}' > "$5";;
 *" pull "*) echo fake-elf > "$5";;
esac
""",
            "bin/file": '#!/bin/sh\necho "ELF 64-bit ARM aarch64"\n',
            "bin/readelf": """#!/bin/sh
case "$1" in --version-info) echo GLIBC_2.17;; -s) echo kbase_kmod_ops;; esac
""",
        }
        for name, content in commands.items():
            path = project / name
            path.write_text(content)
            path.chmod(0o755)
        env = dict(self.env, PATH=f"{project / 'bin'}:{self.env['PATH']}",
                   ADB_LOG=str(project / "adb.log"))

        def build(*args, **extra):
            return subprocess.run(
                ["sh", str(project / "scripts/build-glibc.sh"), "--profile",
                 "g615-v11-csf", "--serial", "fake", *args],
                env=dict(env, **extra), capture_output=True, text=True)

        failure = build(FAIL_PULL="1")
        self.assertNotEqual(failure.returncode, 0, failure.stdout + failure.stderr)
        self.assertFalse((project / "dist/glibc-g615-v11-csf").exists())
        default = build()
        self.assertEqual(default.returncode, 0, default.stdout + default.stderr)
        sync = build("--with-kbase-sync")
        self.assertEqual(sync.returncode, 0, sync.stdout + sync.stderr)
        default_source_id = default.stdout.split("source_id=", 1)[1].split()[0]
        sync_source_id = sync.stdout.split("source_id=", 1)[1].split()[0]
        self.assertNotEqual(default_source_id, sync_source_id)
        outputs = list((project / "dist").iterdir())
        self.assertEqual(len(outputs), 2)
        self.assertEqual(len({json.loads((x / "series-manifest.json").read_text())["variant"]
                              for x in outputs}), 2)
        again = build()
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("destination already exists", again.stderr)


if __name__ == "__main__":
    unittest.main()
