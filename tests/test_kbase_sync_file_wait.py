"""Compile sync_file polling with deterministic deadline and poll stubs."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches/experimental-kbase-sync/007-kbase-sync-file-poll-deadlines.patch"


def wait_function():
    source = os.environ.get("PANVK_SYNC_FILE_WAIT_SOURCE")
    if source:
        text = Path(source).read_text()
    else:
        patch = PATCH if PATCH.exists() else ROOT / "patches/kbase-common/004-physical-device-kbase.patch"
        text = "\n".join(
            line[1:] for line in patch.read_text().splitlines()
            if line.startswith(("+", " ")) and not line.startswith("+++")
        )
    match = re.search(r"kbase_sync_file_wait_func\(void \*data,[^;]*?\)\s*\{", text)
    if match is None:
        raise AssertionError("sync_file wait definition not found")
    start = match.start()
    opening = match.end() - 1
    depth, end = 1, opening + 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return "static VkResult\n" + text[start:end]


class SyncFileWaitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        source = Path(cls.temp.name) / "wait.c"
        cls.exe = Path(cls.temp.name) / "wait"
        source.write_text(r"""
#include <assert.h>
#include <errno.h>
#include <limits.h>
#include <poll.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef int VkResult;
#define UNUSED __attribute__((unused))
#define MIN2(a,b) ((a) < (b) ? (a) : (b))
#define VK_SUCCESS 0
#define VK_TIMEOUT 2
#define VK_ERROR_UNKNOWN (-13)
#define VK_ERROR_DEVICE_LOST (-4)
#define VK_ERROR_INVALID_EXTERNAL_HANDLE (-1000072003)
struct kbase_sync_file_waiter { int fd; };
struct poll_step { int ret; short revents; int error; uint64_t elapsed; };
static struct poll_step steps[3];
static int timeouts[3];
static unsigned count, calls, logs;
static uint64_t now;
static uint64_t os_time_get_nano(void) { return now; }
static void __attribute__((unused)) test_log(const char *format, ...) {
   (void)format; logs++;
}
#define mesa_loge test_log
static int fake_poll(struct pollfd *pfd, nfds_t nfds, int timeout) {
   assert(nfds == 1 && calls < count);
   assert(pfd->fd == 42 && (pfd->events & POLLIN));
   assert(timeout == timeouts[calls]);
   struct poll_step step = steps[calls++];
   now += step.elapsed;
   pfd->revents = step.revents;
   errno = step.error;
   return step.ret;
}
#define poll fake_poll
""" + wait_function() + r"""
int main(int argc, char **argv) {
   assert(argc == 2);
   int scenario = atoi(argv[1]);
   struct kbase_sync_file_waiter waiter = {.fd = 42};
   uint64_t deadline = 0;
   VkResult expected = VK_SUCCESS;
   unsigned expected_logs = 0;
   count = 1;
   steps[0] = (struct poll_step){1, POLLIN, 0, 0};
   switch (scenario) {
   case 0:
      waiter.fd = -1; count = 0;
      expected = VK_ERROR_INVALID_EXTERNAL_HANDLE; expected_logs = 1; break;
   case 1: break;
   case 2:
      steps[0].revents = POLLNVAL;
      expected = VK_ERROR_INVALID_EXTERNAL_HANDLE; expected_logs = 1; break;
   case 3:
      steps[0].revents = POLLERR;
      expected = VK_ERROR_DEVICE_LOST; expected_logs = 1; break;
   case 4:
      steps[0].revents = POLLHUP;
      expected = VK_ERROR_DEVICE_LOST; expected_logs = 1; break;
   case 5:
      steps[0].revents = POLLIN | POLLERR;
      expected = VK_ERROR_DEVICE_LOST; expected_logs = 1; break;
   case 6:
      steps[0].revents = POLLPRI;
      expected = VK_ERROR_UNKNOWN; expected_logs = 1; break;
   case 7:
      steps[0].revents = 0;
      expected = VK_ERROR_UNKNOWN; expected_logs = 1; break;
   case 8:
      steps[0] = (struct poll_step){-1, 0, EIO, 0};
      expected = VK_ERROR_UNKNOWN; expected_logs = 1; break;
   case 9:
   case 10:
      now = 100; deadline = scenario == 9 ? 0 : 99;
      steps[0].ret = 0; expected = VK_TIMEOUT; break;
   case 11:
   case 12:
   case 14:
      deadline = 6000000; count = 2;
      timeouts[0] = 6; timeouts[1] = 4;
      steps[0] = (struct poll_step){-1, 0, scenario == 12 ? EAGAIN : EINTR, 2000000};
      steps[1] = (struct poll_step){0, 0, 0, 4000000};
      expected = VK_TIMEOUT;
      if (scenario == 14) {
         steps[1] = (struct poll_step){1, POLLIN, 0, 1000000};
         expected = VK_SUCCESS;
      }
      break;
   case 13:
      steps[0] = (struct poll_step){-1, 0, EINTR, 0};
      expected = VK_TIMEOUT; break;
   case 15:
      deadline = 17000; timeouts[0] = 1;
      steps[0] = (struct poll_step){0, 0, 0, 17000};
      expected = VK_TIMEOUT; break;
   case 16:
   case 21:
      deadline = ((uint64_t)INT_MAX + 1) * 1000000; count = 2;
      timeouts[0] = INT_MAX; timeouts[1] = 1;
      steps[0] = (struct poll_step){0, 0, 0, (uint64_t)INT_MAX * 1000000};
      steps[1] = (struct poll_step){0, 0, 0, 1000000};
      expected = VK_TIMEOUT;
      if (scenario == 21) {
         steps[1].ret = 1; steps[1].revents = POLLIN;
         expected = VK_SUCCESS;
      }
      break;
   case 17:
      deadline = UINT64_MAX - 1; timeouts[0] = INT_MAX; break;
   case 18:
      deadline = UINT64_MAX; count = 2;
      timeouts[0] = timeouts[1] = -1;
      steps[0] = (struct poll_step){-1, 0, EINTR, 6000000};
      steps[1] = (struct poll_step){1, POLLIN, 0, 0}; break;
   case 19:
      deadline = 1000001; count = 2;
      timeouts[0] = 2; timeouts[1] = 1;
      steps[0] = (struct poll_step){0, 0, 0, 500000};
      steps[1] = (struct poll_step){0, 0, 0, 500001};
      expected = VK_TIMEOUT; break;
   case 20:
      deadline = 1000000; count = 2;
      timeouts[0] = timeouts[1] = 1;
      steps[0] = (struct poll_step){-1, 0, EINTR, 600000};
      steps[1] = (struct poll_step){-1, 0, EAGAIN, 600000};
      expected = VK_TIMEOUT; break;
   case 22:
      steps[0].revents = POLLIN | POLLNVAL;
      expected = VK_ERROR_INVALID_EXTERNAL_HANDLE; expected_logs = 1; break;
   default: return 2;
   }
   assert(kbase_sync_file_wait_func(&waiter, NULL, deadline) == expected);
   assert(calls == count && logs == expected_logs);
   return 0;
}
""")
        subprocess.run(
            [os.environ.get("CC", "cc"), "-std=c11", "-Wall", "-Wextra",
             "-Werror", str(source), "-o", str(cls.exe)], check=True)

    def run_scenarios(self, scenarios):
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                result = subprocess.run([str(self.exe), str(scenario)], timeout=5,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_revents_and_errors_are_not_success(self):
        self.run_scenarios([0, 1, 2, 3, 4, 5, 6, 7, 8, 22])

    def test_retries_respect_absolute_deadline(self):
        self.run_scenarios([9, 10, 11, 12, 13, 14, 19, 20])

    def test_sub_ms_and_long_finite_timeouts(self):
        self.run_scenarios([15, 16, 17, 18, 21])


if __name__ == "__main__":
    unittest.main()
