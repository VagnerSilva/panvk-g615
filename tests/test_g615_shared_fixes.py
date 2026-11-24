import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MESA = Path(os.environ.get("PANVK_MESA_SOURCE", ROOT / "work/mesa"))


def run_c(source):
    with tempfile.TemporaryDirectory(prefix="panvk-g615-shared-") as temp:
        code = Path(temp) / "test.c"
        binary = Path(temp) / "test"
        code.write_text(source)
        result = subprocess.run(
            [os.environ.get("CC", "cc"), "-std=gnu11", "-Wall", "-Werror",
             str(code), "-o", str(binary)], capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        subprocess.run([str(binary)], check=True)


class G615SharedFixTests(unittest.TestCase):
    def test_memory_budget_uses_the_kbase_character_node(self):
        source = (MESA / "src/panfrost/vulkan/panvk_physical_device.c").read_text()
        start = source.index("   dev_t budget_rdev = device->drm.render_rdev;")
        end = source.index("      return VK_ERROR_OUT_OF_HOST_MEMORY;", start)
        block = source[start:end + len("      return VK_ERROR_OUT_OF_HOST_MEMORY;")]
        run_c(r"""
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <sys/stat.h>
#include <sys/types.h>
#define HAVE_PAN_KMOD_KBASE 1
#define VK_ERROR_INITIALIZATION_FAILED (-3)
#define VK_ERROR_OUT_OF_HOST_MEMORY (-1)
static struct stat next_stat;
static int stat_error, budget_calls, errors;
static dev_t budget_key;
static bool oom;
static int budget;
static int fake_fstat(int fd, struct stat *st)
{
   assert(fd == 42);
   *st = next_stat;
   return stat_error;
}
#define fstat fake_fstat
#define vk_errorf(instance, code, ...) (++errors, code)
static void *get_memory_budget(dev_t key)
{
   budget_calls++;
   budget_key = key;
   return oom ? NULL : &budget;
}
struct test_device {
   struct { dev_t render_rdev; } drm;
   struct { struct { int fd; } *dev; } kmod;
   char kbase_node_path[16];
   struct { void *budget; } memory;
};
static int init(struct test_device *device)
{
""" + block + r"""
   return 0;
}
int main(void)
{
   struct test_device device = { .drm.render_rdev = 17,
                                .kbase_node_path = "/dev/mali0" };
   typeof(*device.kmod.dev) kmod = { .fd = 42 };
   device.kmod.dev = &kmod;
   next_stat.st_mode = S_IFCHR | 0600;
   next_stat.st_rdev = 99;
   assert(init(&device) == 0);
   assert(budget_key == 99 && device.memory.budget == &budget);
   stat_error = -1;
   assert(init(&device) == VK_ERROR_INITIALIZATION_FAILED);
   assert(budget_calls == 1 && errors == 1);
   stat_error = 0;
   next_stat.st_mode = S_IFREG | 0600;
   assert(init(&device) == VK_ERROR_INITIALIZATION_FAILED);
   assert(budget_calls == 1 && errors == 2);
   next_stat.st_mode = S_IFCHR | 0600;
   oom = true;
   assert(init(&device) == VK_ERROR_OUT_OF_HOST_MEMORY);
   assert(device.memory.budget == NULL);
   return 0;
}
""")

    def test_xcb_event_symbols_are_resolved_by_the_real_loader(self):
        source = (MESA / "src/vulkan/wsi/wsi_x11_dlopen.c").read_text()
        source = re.sub(r"^#include .*\n", "", source, flags=re.MULTILINE)
        asm = source.index('   __asm__(".text\\n"')
        start = source.rfind("#define S(sym)", 0, asm)
        end = source.index("#undef S", asm) + len("#undef S")
        source = source[:start] + source[end:]
        run_c(r"""
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
#define RTLD_NOW 1
#define RTLD_LOCAL 0
#define mesa_loge(...) ((void)fprintf(stderr, __VA_ARGS__))
typedef struct { const char *name; int global_id; } xcb_extension_t;
typedef int once_flag;
#define ONCE_FLAG_INIT 0
static void call_once(once_flag *once, void (*fn)(void))
{
   if (!*once) { *once = 1; fn(); }
}
static int marker;
static unsigned observed;
static void *dlopen(const char *name, int flags) { return &marker; }
static const char *dlerror(void) { return "mock loader"; }
static void *dlsym(void *handle, const char *name)
{
   if (!strcmp(name, "xcb_connect")) observed |= 1;
   if (!strcmp(name, "xcb_connection_has_error")) observed |= 2;
   if (!strcmp(name, "xcb_disconnect")) observed |= 4;
   if (!strcmp(name, "xcb_get_file_descriptor")) observed |= 8;
   return &marker;
}
""" + source + r"""
int main(void)
{
   assert(wsi_x11_dlopen());
   assert(observed == 15);
   assert(wsi_x11_dl_xcb_connect == &marker);
   assert(wsi_x11_dl_xcb_connection_has_error == &marker);
   assert(wsi_x11_dl_xcb_disconnect == &marker);
   assert(wsi_x11_dl_xcb_get_file_descriptor == &marker);
   return 0;
}
""")


if __name__ == "__main__":
    unittest.main()
