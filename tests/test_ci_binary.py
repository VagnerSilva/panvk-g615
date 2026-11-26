import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BinaryValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.binary = self.root / "driver.so"
        self.binary.write_bytes(b"fixture")
        for name, body in {
            "file": 'echo "ELF fixture"',
            "readelf": '''
case "$1" in
  -h) printf '  Class: %s\\n  Machine: %s\\n  Type: %s\\n  Data: %s\\n' "${ELF_CLASS:-ELF64}" "${ELF_MACHINE:-AArch64}" "${ELF_TYPE:-DYN}" "${ELF_ENDIAN:-little endian}";;
  -d) echo 'NEEDED libc.so.6';;
esac
''',
            "llvm-nm": '''
echo 'T vk_icdGetInstanceProcAddr'
[ "${MISSING_EXPORT:-0}" = 1 ] || echo 'T vk_icdNegotiateLoaderICDInterfaceVersion'
''',
        }.items():
            path = self.root / name
            path.write_text("#!/bin/sh\n" + body + "\n")
            path.chmod(0o755)
        self.env = {**os.environ, "PATH": f"{self.root}:{os.environ['PATH']}"}

    def validate(self, **env):
        return subprocess.run(
            ["sh", str(ROOT / "scripts/validate-binary.sh"), "--abi",
             env.pop("abi", "glibc"), str(self.binary)],
            env={**self.env, **env}, capture_output=True, text=True,
        )

    def test_non_aarch64_or_non_elf64_binary_cannot_pass(self):
        for env in ({"ELF_MACHINE": "Advanced Micro Devices X86-64"}, {"ELF_CLASS": "ELF32"},
                    {"ELF_TYPE": "REL"}, {"ELF_ENDIAN": "big endian"}):
            with self.subTest(env=env):
                result = self.validate(**env)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("FAIL", result.stdout + result.stderr)

    def test_glibc_requires_both_icd_exports(self):
        self.assertEqual(self.validate().returncode, 0)
        result = self.validate(MISSING_EXPORT="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("vk_icdNegotiateLoaderICDInterfaceVersion", result.stdout + result.stderr)

    def test_unknown_abi_is_rejected(self):
        result = self.validate(abi="unknown")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
