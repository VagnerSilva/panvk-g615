#!/usr/bin/env python3
"""Test the ANB dma-buf fd finder in the G615 profile series."""

from pathlib import Path
import os
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches/android/018-vulkan-android-find-dma-buf-among-anb-handle-fds.patch"
NAME = "vk_android_find_anb_dma_buf_fd"


def patch_function():
    lines = PATCH.read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if line == f"+{NAME}(struct vk_device *device,")
    end = next(i for i in range(start, len(lines)) if lines[i] == "+}")
    return "static int\n" + "\n".join(line[1:] for line in lines[start:end + 1])


class AnbDmaBufFdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        source = Path(cls.tmp.name) / "anb.c"
        cls.exe = Path(cls.tmp.name) / "anb"
        source.write_text(
            r"""
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>
typedef int VkResult;
typedef void *VkDevice;
typedef int VkExternalMemoryHandleTypeFlagBits;
typedef struct { int memoryTypeBits; } VkMemoryFdPropertiesKHR;
#define VK_SUCCESS 0
#define VK_ERROR_INVALID_EXTERNAL_HANDLE (-1000072003)
#define VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT 0x200
typedef struct { int version, numFds, numInts; int data[4]; } native_handle_t;
static int rejected_fd = -1;
static VkResult get_props(VkDevice dev, VkExternalMemoryHandleTypeFlagBits type,
                          int fd, VkMemoryFdPropertiesKHR *props)
{
   if (fd == rejected_fd)
      return VK_ERROR_INVALID_EXTERNAL_HANDLE;
   props->memoryTypeBits = 1;
   return VK_SUCCESS;
}
struct vk_device {
   struct {
      VkResult (*GetMemoryFdPropertiesKHR)(VkDevice, VkExternalMemoryHandleTypeFlagBits,
                                           int, VkMemoryFdPropertiesKHR *);
   } dispatch_table;
};
"""
            + patch_function()
            + r"""
static int sized_file(void)
{
   FILE *f = tmpfile();
   fputs("dma-buf", f);
   fflush(f);
   return dup(fileno(f));
}
int main(void)
{
   struct vk_device dev = { { get_props } };
   VkMemoryFdPropertiesKHR props = { 0 };
   int p[2];
   if (pipe(p))
      return 2;
   int empty = fileno(tmpfile());
   int good = sized_file(), rejected = sized_file();
   rejected_fd = rejected;

   /* MediaTek layout: gralloc_extra (unseekable) before the dma-buf. */
   native_handle_t mtk = { sizeof(native_handle_t), 2, 0, { p[0], good } };
   if (vk_android_find_anb_dma_buf_fd(&dev, &mtk, &props) != good || props.memoryTypeBits != 1)
      return 3;

   native_handle_t first = { sizeof(native_handle_t), 2, 0, { good, p[0] } };
   if (vk_android_find_anb_dma_buf_fd(&dev, &first, &props) != good)
      return 4;

   native_handle_t skips = { sizeof(native_handle_t), 4, 0, { -1, empty, rejected, good } };
   if (vk_android_find_anb_dma_buf_fd(&dev, &skips, &props) != good)
      return 5;

   native_handle_t none = { sizeof(native_handle_t), 3, 0, { p[0], empty, rejected } };
   if (vk_android_find_anb_dma_buf_fd(&dev, &none, &props) != -1)
      return 6;

   /* Integers after numFds must never be treated as fds. */
   native_handle_t ints = { sizeof(native_handle_t), 1, 1, { p[0], good } };
   if (vk_android_find_anb_dma_buf_fd(&dev, &ints, &props) != -1)
      return 7;
   return 0;
}
"""
        )
        subprocess.run(["cc", "-std=c11", "-D_GNU_SOURCE", "-Wall", "-Werror",
                        "-Wno-unused-parameter", str(source), "-o", str(cls.exe)],
                       check=True)

    def test_finder(self):
        self.assertEqual(subprocess.run([str(self.exe)]).returncode, 0)

    def test_import_uses_finder_instead_of_data0(self):
        text = PATCH.read_text()
        self.assertIn("-   int dma_buf_fd = anb->handle->data[0];", text)
        self.assertIn("+      vk_android_find_anb_dma_buf_fd(device, anb->handle, &fd_props);", text)

    def test_patch_series_selects_correct_port(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            git = tmp / "git"
            git.write_text(
                '#!/bin/sh\n'
                'printf "%s\\n" "$*" >> "$TEST_GIT_LOG"\n'
                'case " $* " in *" rev-parse "*) echo 5a07217f;; esac\n'
            )
            git.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{tmp}{os.pathsep}{env['PATH']}"
            env["TEST_GIT_LOG"] = str(tmp / "git.log")

            def replay(script, *args):
                mesa = tmp / "mesa"
                mesa.mkdir(exist_ok=True)
                (tmp / "git.log").write_text("")
                subprocess.run(
                    ["sh", str(ROOT / "scripts" / script), "--mesa", str(mesa), *args],
                    env=env, check=True, stdout=subprocess.DEVNULL,
                )
                return (tmp / "git.log").read_text().splitlines()

            main = replay("apply-patches.sh", "--profile", "g615-v11-csf")
            self.assertEqual(sum(f"apply {PATCH}" in line for line in main), 1)
            self.assertFalse(any("/patches/jm-v7-wip/" in line for line in main))
            self.assertFalse(any("/patches/jm-v9/" in line or "/patches/jm-v7/" in line
                                 for line in main))
            experimental = ROOT / "patches/experimental-kbase-sync"
            self.assertFalse(any(str(experimental) in line for line in main))

            opted_in = replay("apply-patches.sh", "--profile", "g615-v11-csf",
                              "--with-kbase-sync")
            sync_patches = [
                experimental / "002-android-release-queue-mesa27.patch",
                experimental / "003-kbase-coalesce-mem-sync.patch",
                experimental / "004-kbase-sync-file-waiter-lifetime.patch",
            ]
            applied = [line for line in opted_in if line.startswith("-C ") and
                       f" apply {experimental}/" in line]
            self.assertEqual(len(applied), 3)
            for line, patch in zip(applied, sync_patches):
                self.assertIn(f"apply {patch}", line)
            self.assertGreater(
                opted_in.index(applied[0]),
                max(i for i, line in enumerate(opted_in)
                    if " apply " in line and "/patches/csf-v11/" in line),
            )

            rejected = subprocess.run(
                ["sh", str(ROOT / "scripts/apply-patches.sh"),
                 "--profile", "g610-v10-csf", "--with-kbase-sync",
                 "--mesa", str(tmp / "mesa")],
                env=env, capture_output=True, text=True,
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("requires --profile g615-v11-csf", rejected.stderr)

if __name__ == "__main__":
    unittest.main()
