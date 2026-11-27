"""Compile the patched WAIT_ANY function with deterministic clock/sync stubs."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
NAME = "kbase_cpu_sync_wait_many"


def wait_function():
    source = os.environ.get("PANVK_WAIT_ANY_SOURCE")
    if source:
        text = Path(source).read_text()
    else:
        base = ROOT / "patches/kbase-common/004-physical-device-kbase.patch"
        text = "\n".join(line[1:] for line in base.read_text().splitlines()
                         if line.startswith("+") and not line.startswith("+++"))
        patch = ROOT / "patches/experimental-kbase-sync/005-kbase-avoid-wait-any-spin.patch"
        hunks = patch.read_text().split("\n@@ ")[1:]
        for hunk in hunks:
            lines = hunk.splitlines()[1:]
            old = "\n".join(line[1:] for line in lines if line.startswith((" ", "-")))
            new = "\n".join(line[1:] for line in lines if line.startswith((" ", "+")))
            if NAME in hunk.splitlines()[0]:
                if old not in text:
                    raise AssertionError("WAIT_ANY patch context does not match its base")
                text = text.replace(old, new, 1)
    start = text.index(NAME + "(struct vk_device *device,\n")
    end = text.index("\n}", start) + 2
    return "static VkResult\n" + text[start:end]


class WaitAnyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        source = Path(cls.temp.name) / "wait.c"
        cls.exe = Path(cls.temp.name) / "wait"
        source.write_text(r"""
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <errno.h>
#include <sched.h>
#include <time.h>
#include <stdlib.h>
typedef int VkResult;
#define VK_SUCCESS 0
#define VK_TIMEOUT 2
#define VK_ERROR_UNKNOWN (-13)
#define MIN2(a, b) ((a) < (b) ? (a) : (b))
#define container_of(ptr, type, member) ((type *)((char *)(ptr) - offsetof(type, member)))
enum vk_sync_wait_flags { VK_SYNC_WAIT_ANY = 1 };
struct vk_device { int unused; };
struct vk_sync { int unused; };
struct kbase_cpu_sync { struct vk_sync sync; VkResult result; uint64_t ready; };
struct vk_sync_wait { struct vk_sync *sync; };
static uint64_t now, delays[32];
static unsigned sleeps, polls, errors;
static int sleep_error;
static uint64_t os_time_get_nano(void) { return now; }
static VkResult vk_errorf(struct vk_device *device, VkResult result,
                         const char *format, ...)
{
   (void)device; (void)format; errors++; return result;
}
static VkResult kbase_cpu_sync_wait_one(struct vk_device *device,
   struct kbase_cpu_sync *sync, enum vk_sync_wait_flags flags, uint64_t timeout)
{
   (void)device; (void)flags;
   assert(++polls < 100);
   if (timeout && sync->ready <= timeout)
      now = sync->ready;
   return sync->result == VK_SUCCESS && now < sync->ready ? VK_TIMEOUT : sync->result;
}
static int fake_nanosleep(const struct timespec *req, struct timespec *rem)
{
   (void)rem;
   assert(sleeps < 32 && req->tv_sec == 0);
   delays[sleeps++] = req->tv_nsec;
   if (sleep_error) {
      errno = sleep_error;
      sleep_error = 0;
      now += 1000;
      return -1;
   }
   now += req->tv_nsec;
   return 0;
}
#define nanosleep fake_nanosleep
""" + wait_function() + r"""
int main(int argc, char **argv)
{
   assert(argc == 2);
   int test = atoi(argv[1]);
   struct vk_device device = {0};
   struct kbase_cpu_sync sync[2] = {
      { {0}, VK_TIMEOUT, 0 }, { {0}, VK_SUCCESS, 4000000 }
   };
   struct vk_sync_wait waits[2] = { { &sync[0].sync }, { &sync[1].sync } };
   uint64_t deadline = UINT64_MAX;
   enum vk_sync_wait_flags flags = VK_SYNC_WAIT_ANY;
   VkResult expected = VK_SUCCESS;
   now = 100;
   switch (test) {
   case 0: sync[1].ready = 0; break;
   case 1: deadline = 0; expected = VK_TIMEOUT; break;
   case 2: deadline = now; expected = VK_TIMEOUT; break;
   case 3: deadline = now + 17000; expected = VK_TIMEOUT; break;
   case 4: break;
   case 5: sleep_error = EINTR; deadline = now + 17000; expected = VK_TIMEOUT; break;
   case 6: sleep_error = EINVAL; expected = VK_ERROR_UNKNOWN; break;
   case 7: sync[0].result = VK_ERROR_UNKNOWN; expected = VK_ERROR_UNKNOWN; break;
   case 8: flags = 0; sync[0].result = VK_SUCCESS; sync[1].ready = 500; deadline = 1000; break;
   default: return 2;
   }
   assert(kbase_cpu_sync_wait_many(&device, 2, waits, flags, deadline) == expected);
   if (test <= 2 || test == 7 || test == 8)
      assert(sleeps == 0);
   if (test == 3)
      assert(sleeps == 1 && delays[0] == 17000 && now == deadline);
   if (test == 4) {
      const uint64_t expected_delays[] = {50000, 100000, 200000, 400000, 800000, 1000000, 1000000, 1000000};
      assert(sleeps == 8);
      for (unsigned i = 0; i < sleeps; i++)
         assert(delays[i] == expected_delays[i]);
   }
   if (test == 5)
      assert(sleeps == 2 && delays[1] == 16000 && now == deadline);
   if (test == 6)
      assert(sleeps == 1 && errors == 1);
   return 0;
}
""")
        subprocess.run(["cc", "-std=c11", "-D_POSIX_C_SOURCE=200809L", "-Wall",
                        "-Werror", "-Wno-unused-function", str(source), "-o", str(cls.exe)],
                       check=True)

    def test_wait_semantics_and_bounded_backoff(self):
        for case in range(9):
            with self.subTest(case=case):
                result = subprocess.run([str(self.exe), str(case)], timeout=5,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
