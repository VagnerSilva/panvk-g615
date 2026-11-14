#!/usr/bin/env python3
"""Execute the tiler option resolver exported by patch 0177."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches/jm-v7-wip/0177-panvk-csf-g615-conservative-tiler-defaults.patch"


def patch_function(name):
    lines = PATCH.read_text().splitlines()
    start = next(
        i for i, line in enumerate(lines)
        if line.startswith((f"+{name}(", f" {name}("))
    )
    end = next(i for i in range(start, len(lines)) if lines[i] in ("+}", " }"))
    return "static void\n" + "\n".join(
        line[1:] for line in lines[start:end + 1] if line.startswith(("+", " "))
    )


class TilerDefaultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        source = Path(cls.tmp.name) / "tiler.c"
        cls.exe = Path(cls.tmp.name) / "tiler"
        source.write_text(
            r"""
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MIN2(a, b) ((a) < (b) ? (a) : (b))
#define MAX2(a, b) ((a) > (b) ? (a) : (b))
#define PAN_PROD_ID(a, b, c) (((a) << 16) | ((b) << 8) | (c))
#define mesa_logi(...) ((void)0)
struct pan_model { uint32_t gpu_prod_id; };
struct panvk_physical_device {
   const struct pan_model *model;
   struct {
      bool kbase_tiler_ir;
      struct {
         uint32_t initial_chunks, max_chunks, chunk_size;
      } tiler;
   } csf;
};
static const char *os_get_option(const char *name) { return getenv(name); }
static bool debug_get_bool_option(const char *name, bool fallback)
{
   assert(!strcmp(name, "PANVK_KBASE_TILER_IR"));
   const char *e = getenv(name);
   return e ? strcmp(e, "0") != 0 : fallback;
}
"""
            + patch_function("kbase_init_tiler_options")
            + "\n"
            + patch_function("kbase_heap_chunks")
            + r"""
int main(int argc, char **argv)
{
   assert(argc > 1 && (argc - 1) % 2 == 0);
   for (int n = 1; n < argc; n += 2) {
      struct pan_model model = {strtoul(argv[n + 1], NULL, 0)};
      struct panvk_physical_device device = {
         .model = &model,
         .csf.tiler = {10, 400, 1024 * 1024},
      };
      kbase_init_tiler_options(&device, strtoul(argv[n], NULL, 0));
      uint32_t initial, max;
      kbase_heap_chunks(&device, &initial, &max);
      assert(initial == device.csf.tiler.initial_chunks);
      assert(max == device.csf.tiler.max_chunks);
      printf("%d %u %u\n", device.csf.kbase_tiler_ir, initial, max);
   }
   return 0;
}
"""
        )
        subprocess.run(
            ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", str(source),
             "-o", str(cls.exe)],
            check=True,
        )

    def resolve(self, devices=((11, 0xB0803),), ir=None, chunks=None):
        env = os.environ.copy()
        for name, value in (("PANVK_KBASE_TILER_IR", ir),
                            ("PANVK_KBASE_HEAP_CHUNKS", chunks)):
            env.pop(name, None)
            if value is not None:
                env[name] = value
        args = [arg for arch, product in devices for arg in (str(arch), hex(product))]
        result = subprocess.run(
            [str(self.exe), *args], env=env, check=True, text=True,
            capture_output=True,
        )
        return [tuple(map(int, line.split())) for line in result.stdout.splitlines()]

    def test_g615_defaults(self):
        self.assertEqual(self.resolve(), [(0, 10, 400)])

    def test_real_model_lookup_across_revisions(self):
        mesa = ROOT / "work/mesa-universal"
        model = mesa / "src/panfrost/model/pan_model.c"
        if not model.exists():
            self.skipTest("prepared Mesa tree is not available")
        source = Path(self.tmp.name) / "model.c"
        exe = Path(self.tmp.name) / "model"
        source.write_text(
            r"""
#include <assert.h>
#include <stdio.h>
#include "panfrost/model/pan_model.h"
int main(void)
{
   const uint64_t ids[] = {0xb8a30000, 0xb8a31030, 0xb8a3ffff, 0xb8a21030};
   for (unsigned i = 0; i < sizeof(ids) / sizeof(ids[0]); i++) {
      const struct pan_model *model = pan_get_model(ids[i], 4);
      assert(model);
      printf("%u\n", model->gpu_prod_id);
   }
   return 0;
}
"""
        )
        subprocess.run(
            ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
             "-I", str(mesa / "include"), "-I", str(mesa / "src"),
             str(source), str(model), "-o", str(exe)],
            check=True,
        )
        products = subprocess.run(
            [str(exe)], check=True, text=True, capture_output=True,
        ).stdout.splitlines()
        self.assertEqual(list(map(int, products)), [0xB0803] * 3 + [0xB0802])
        self.assertEqual(
            self.resolve(tuple((11, int(product)) for product in products)),
            [(0, 10, 400)] * 3 + [(1, 4, 400)],
        )

    def test_other_arch_defaults(self):
        for arch in (10, 11, 12, 13, 14):
            with self.subTest(arch=arch):
                self.assertEqual(
                    self.resolve(((arch, (arch << 16) | 0x802),)),
                    [(int(arch in (11, 12, 13)), 4, 400)],
                )

    def test_device_defaults_are_not_process_cached(self):
        g615, g715 = (11, 0xB0803), (11, 0xB0802)
        self.assertEqual(
            self.resolve((g615, g715, g615)), [(0, 10, 400), (1, 4, 400), (0, 10, 400)]
        )
        self.assertEqual(self.resolve((g715, g615)), [(1, 4, 400), (0, 10, 400)])

    def test_ir_overrides(self):
        for ir in ("0", "1"):
            with self.subTest(ir=ir):
                self.assertEqual(
                    self.resolve(((11, 0xB0803), (11, 0xB0802), (14, 0xE0800)), ir=ir),
                    [(int(ir), 10, 400), (int(ir), 4, 400), (int(ir), 4, 400)],
                )

    def test_heap_overrides(self):
        cases = {
            "4,32": (4, 32), "10,400": (10, 400), "7": (7, 400),
            "100,32": (32, 32), "1,8": (1, 8), "1024,4096": (1024, 4096),
            "0,7": (10, 400), "1025,4097": (10, 400), "": (10, 400),
        }
        for chunks, expected in cases.items():
            with self.subTest(chunks=chunks):
                self.assertEqual(self.resolve(chunks=chunks), [(0, *expected)])

    def test_overrides_are_independent(self):
        self.assertEqual(self.resolve(ir="1"), [(1, 10, 400)])
        self.assertEqual(self.resolve(chunks="4,32"), [(0, 4, 32)])
        self.assertEqual(self.resolve(ir="1", chunks="4,32"), [(1, 4, 32)])

    def test_all_consumers_share_physical_settings(self):
        patch = PATCH.read_text()
        added = "\n".join(line[1:] for line in patch.splitlines() if line.startswith("+"))
        self.assertIn("const bool one_group = phys_dev->csf.kbase_tiler_ir;", added)
        self.assertIn("!heap_stats && !phys_dev->csf.kbase_tiler_ir", added)
        self.assertNotIn("DEBUG_GET_ONCE_BOOL_OPTION", added)
        self.assertNotIn("static uint32_t init_v, max_v", added)
        self.assertIn("kbase_init_tiler_options(device, arch);", added)
        self.assertIn("device->model->gpu_prod_id == PAN_PROD_ID(11, 8, 3)", added)
        self.assertNotIn("core_count", added)
        self.assertNotIn("gpu_variant", added)
        # Existing heap sites remain untouched and continue using the one accessor.
        old = (ROOT / "patches/csf-v11/224-smaller-kbase-tiler-heaps-and-bounded-term-backlog.patch").read_text()
        self.assertEqual(old.count("+   kbase_heap_chunks(phys_dev,"), 2)
        self.assertIn("+      kbase_heap_chunks(phys_dev,", old)
        self.assertIn("const bool heap_stats = !cmdbuf_skips_gpu_heap_ops(cmdbuf);", patch)
        # The new initialization call is inside the kbase-only arch >= 10 block.
        self.assertIn("panvk_physical_device_init_kbase", patch)
        self.assertIn("device->csf.tiler.max_chunks = 400;", patch)


if __name__ == "__main__":
    unittest.main()
