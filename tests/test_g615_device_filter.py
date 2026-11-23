import os
import re
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches/csf-v11/234-restrict-kbase-panvk-to-g615.patch"
MESA = Path(os.environ.get("PANVK_MESA_SOURCE", ROOT / "work/mesa"))


def extract_function(source, name):
    match = re.search(r"\bstatic\s+bool\s+" + re.escape(name) + r"\s*\(", source)
    if match is None:
        raise AssertionError(f"missing {name} in patched Mesa source")

    start = source.find("{", match.end())
    if start < 0:
        raise AssertionError(f"missing function body for {name}")

    depth = 0
    for offset in range(start, len(source)):
        if source[offset] == "{":
            depth += 1
        elif source[offset] == "}":
            depth -= 1
            if depth == 0:
                return source[match.start() : offset + 1]

    raise AssertionError(f"unterminated function body for {name}")


@contextmanager
def patched_sources():
    if not PATCH.is_file():
        raise AssertionError(f"missing implementation patch: {PATCH}")

    source_files = (
        "src/panfrost/vulkan/panvk_physical_device.c",
        "src/panfrost/vulkan/panvk_instance.c",
    )
    with tempfile.TemporaryDirectory(prefix="panvk-g615-filter-") as temp:
        temp_root = Path(temp)
        for relative in source_files:
            destination = temp_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((MESA / relative).read_bytes())

        physical_device = temp_root / source_files[0]
        if "panvk_is_supported_kbase_model" not in physical_device.read_text():
            check = subprocess.run(
                [
                    "git",
                    "apply",
                    "--check",
                    "--whitespace=error",
                    str(PATCH),
                ],
                cwd=temp_root,
                capture_output=True,
                text=True,
            )
            if check.returncode:
                raise AssertionError(check.stdout + check.stderr)

            subprocess.run(["git", "apply", str(PATCH)], cwd=temp_root, check=True)
        yield temp_root


class G615DeviceFilterTests(unittest.TestCase):
    def test_real_filter_accepts_only_g615_product(self):
        with patched_sources() as mesa:
            source = (mesa / "src/panfrost/vulkan/panvk_physical_device.c").read_text()
            function = extract_function(source, "panvk_is_supported_kbase_model")
            model_header = MESA / "src/panfrost/model/pan_model.h"
            harness = f"""
#include <assert.h>
#include <stdint.h>
#include "{model_header}"

{function}

int main(void)
{{
   const struct pan_model *rev_a = pan_get_model(0xb8a31030, 4, 4, 0);
   const struct pan_model *rev_b = pan_get_model(0xb8a31020, 4, 4, 0);
   const struct pan_model *g715 = pan_get_model(0xb8a21030, 4, 4, 0);
   const struct pan_model *jm = pan_get_model(0x72111010, 0, 4, 0);

   assert(rev_a && rev_b && rev_a == rev_b);
   assert(rev_a->gpu_prod_id == PAN_PROD_ID(11, 8, 3));
   assert(panvk_is_supported_kbase_model(rev_a));
   assert(panvk_is_supported_kbase_model(rev_b));
   assert(g715 && !panvk_is_supported_kbase_model(g715));
   assert(jm && !panvk_is_supported_kbase_model(jm));
   assert(!panvk_is_supported_kbase_model(NULL));
   return 0;
}}
"""
            with tempfile.TemporaryDirectory(prefix="panvk-g615-filter-test-") as temp:
                source_path = Path(temp) / "filter.c"
                binary_path = Path(temp) / "filter"
                source_path.write_text(harness)
                subprocess.run(
                    [
                        os.environ.get("CC", "cc"),
                        "-std=gnu11",
                        "-Wall",
                        "-Werror",
                        f"-I{MESA / 'src'}",
                        f"-I{MESA / 'include'}",
                        str(source_path),
                        str(MESA / "src/panfrost/model/pan_model.c"),
                        "-o",
                        str(binary_path),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                subprocess.run([str(binary_path)], check=True)

    def test_kbase_only_builds_skip_drm_and_keep_kbase_rejection_fallthrough(self):
        for script in ("scripts/build-android.sh", "scripts/build-glibc.sh"):
            self.assertIn("-Dpanfrost-kmds=kbase", (ROOT / script).read_text())

        with patched_sources() as mesa:
            instance = (mesa / "src/panfrost/vulkan/panvk_instance.c").read_text()
            drm_guards = re.findall(
                r"#if defined\(HAVE_PAN_KMOD_PANFROST\)\s*\|\|\s*"
                r"defined\(HAVE_PAN_KMOD_PANTHOR\)(.*?)#endif",
                instance,
                re.DOTALL,
            )
            self.assertTrue(
                any("panvk_physical_device_try_create" in body for body in drm_guards)
            )
            self.assertTrue(any("drmGetDevices2" in body for body in drm_guards))
            self.assertEqual(instance.count("drmGetDevices2"), 1)
            kbase_enumeration = re.search(
                r"#if defined\(HAVE_PAN_KMOD_KBASE\)\s*/\* Enumerate kbase.*?"
                r"^#endif",
                instance,
                re.DOTALL | re.MULTILINE,
            )
            self.assertIsNotNone(kbase_enumeration)
            self.assertRegex(
                kbase_enumeration.group(0),
                r"if\s*\(result\s*==\s*VK_ERROR_INCOMPATIBLE_DRIVER\)\s*"
                r"continue;",
            )


if __name__ == "__main__":
    unittest.main()
