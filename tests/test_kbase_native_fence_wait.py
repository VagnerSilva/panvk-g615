"""Offline syscall tests; never open a real timeline or Mali device."""

from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MOCK = r"""
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <linux/sync_file.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>
#include "drm-uapi/mali_kbase_ioctl.h"

static int scenario, status, queue_live, enqueues, deletes, mali_opens;
static int mali_closes, event_unmaps, cached, has_error;
static int timeline_live, fence_live, failure, stale_done_read;
static int producer_live, producer_enqueues, producer_deletes, creates;
static uint64_t ticks;
static _Alignas(4096) unsigned char cpu[4096], tracking[4096], backing[4096];

static int cqs_input_mode(void)
{
   return scenario >= 28;
}

static void publish(void)
{
   if (!queue_live || enqueues != 3 ||
       (status == 0 && (scenario != 16 || ticks <= 5)) || scenario == 12)
      return;
   uint64_t one = 1;
   uint32_t error = status < 0 && scenario != 13;
   memcpy(backing, &one, 8);
   memcpy(backing + 8, &error, 4);
   memcpy(backing + 64, &one, 8);
   has_error = error;
   if (!cached || scenario == 17)
      memcpy(cpu, backing, sizeof(cpu));
}

static int mock_open(const char *path, int flags, ...)
{
   if (!(flags & O_CLOEXEC))
      failure = 1;
   if (!strcmp(path, "/mock/timeline")) {
      if (scenario == 4 || scenario == 5) {
         errno = scenario == 4 ? ENOENT : EACCES;
         return -1;
      }
      timeline_live = 1;
      status = 0;
      return 10;
   }
   if (strcmp(path, "/dev/mali0"))
      abort();
   mali_opens++;
   if (scenario >= 18)
      status = 0;
   return 30;
}

static int mock_close(int fd)
{
   if (fd == 10) {
      if (!timeline_live)
         failure = 1;
      timeline_live = 0;
      status = scenario == 6 ? 0 : -ENOENT;
      publish();
   } else if (fd == 20) {
      if (!fence_live)
         failure = 1;
      fence_live = 0;
   } else if (fd == 30) {
      if (queue_live || producer_live)
         failure = 1;
      mali_closes++;
   } else {
      abort();
   }
   return 0;
}

static int mock_ioctl(int fd, unsigned long request, ...)
{
   va_list args;
   va_start(args, request);
   void *data = va_arg(args, void *);
   va_end(args);
   if (fd == 10) {
      if (_IOC_NR(request) == 0) {
         /* sw_sync_create_fence_data: value, name[32], fence. */
         int32_t fence = 20;
         memcpy((char *)data + 36, &fence, sizeof(fence));
         fence_live = 1;
      } else if (_IOC_NR(request) == 1) {
         status = 1;
         publish();
      } else {
         abort();
      }
      return 0;
   }
   if (fd == 20 && request == SYNC_IOC_FILE_INFO) {
      ((struct sync_file_info *)data)->status = status;
      return 0;
   }
   if (fd != 30)
      abort();
   if (request == KBASE_IOCTL_CS_EVENT_SIGNAL && scenario >= 18) {
      if (scenario == 25 || scenario == 32) {
         errno = EIO;
         return -1;
      }
      uint64_t value;
      memcpy(&value, (cached ? backing : cpu) + 128, 8);
      if (cqs_input_mode()) {
         uint32_t error;
         memcpy(&error, (cached ? backing : cpu) + 136, 4);
         if (value != 1 || !queue_live || enqueues != 3 ||
             error != (scenario != 29))
            failure = 1;
         status = error ? -EIO : 1;
      } else {
         if (value != 1 || !producer_live || producer_enqueues != 2)
            failure = 1;
         if (scenario != 26)
            status = scenario == 27 ? -EIO : 1;
      }
      publish();
      return 0;
   }
   if (request == KBASE_IOCTL_VERSION_CHECK_CSF) {
      struct kbase_ioctl_version_check *ver = data;
      ver->major = 1;
      ver->minor = scenario == 10 ? 20 : 21;
   } else if (request == KBASE_IOCTL_SET_FLAGS) {
   } else if (request == KBASE_IOCTL_MEM_ALLOC_EX) {
      union kbase_ioctl_mem_alloc_ex *alloc = data;
      cached = !!(alloc->in.flags & BASE_MEM_CACHED_CPU);
      alloc->out.flags = BASE_MEM_SAME_VA | BASE_MEM_CSF_EVENT |
         (cached && scenario != 11 ? BASE_MEM_CACHED_CPU : 0) |
         (scenario == 17 ? BASE_MEM_COHERENT_SYSTEM : 0);
      alloc->out.gpu_va = 0x40000;
   } else if (request == KBASE_IOCTL_MEM_SYNC) {
      if (scenario == 17) {
         errno = EINVAL;
         return -1;
      }
      struct kbase_ioctl_mem_sync *sync = data;
      if (sync->handle != (uintptr_t)cpu ||
          !((sync->size == 128 && sync->user_addr == (uintptr_t)cpu) ||
            (scenario >= 18 && sync->size == 64 &&
             sync->user_addr == (uintptr_t)cpu + 128)))
         failure = 1;
      if (scenario == 24 && sync->size == 64 && cpu[128]) {
         errno = EIO;
         return -1;
      }
      if (sync->type == BASE_SYNCSET_OP_MSYNC) {
         memcpy(backing, cpu, sizeof(cpu));
      } else if (sync->type == BASE_SYNCSET_OP_CSYNC) {
         /* First observation of B exposes an intentionally stale A. */
         if ((scenario == 2 || scenario == 30) &&
             has_error && !stale_done_read) {
            memcpy(cpu + 64, backing + 64, 64);
            stale_done_read = 1;
         } else {
            memcpy(cpu, backing, sizeof(cpu));
         }
      } else {
         abort();
      }
   } else if (request == KBASE_IOCTL_KCPU_QUEUE_CREATE) {
      creates++;
      if (scenario >= 18 && !cqs_input_mode() && creates == 1) {
         ((struct kbase_ioctl_kcpu_queue_new *)data)->id = 8;
         producer_live = 1;
         return 0;
      }
      ((struct kbase_ioctl_kcpu_queue_new *)data)->id = 7;
      queue_live = 1;
   } else if (request == KBASE_IOCTL_KCPU_QUEUE_ENQUEUE) {
      struct kbase_ioctl_kcpu_queue_enqueue *enqueue = data;
      struct base_kcpu_command *cmd = (void *)(uintptr_t)enqueue->addr;
      if (scenario >= 18 && enqueue->id == 8) {
         producer_enqueues++;
         if (enqueue->nr_commands != 1 || !producer_live)
            failure = 1;
         if ((scenario == 21 && producer_enqueues == 1) ||
             (scenario == 22 && producer_enqueues == 2)) {
            errno = ENOMEM;
            return -1;
         }
         if (producer_enqueues == 1) {
            struct base_cqs_wait_operation_info *wait =
               (void *)(uintptr_t)cmd->info.cqs_wait_operation.objs;
            if (cmd->type != BASE_KCPU_COMMAND_TYPE_CQS_WAIT_OPERATION ||
                cmd->info.cqs_wait_operation.nr_objs != 1 ||
                wait->addr != (uintptr_t)cpu + 128 || wait->val != 0 ||
                wait->operation != BASEP_CQS_WAIT_OPERATION_GT ||
                wait->data_type != BASEP_CQS_DATA_TYPE_U64)
               failure = 1;
         } else {
            struct base_fence *fence = (void *)(uintptr_t)cmd->info.fence.fence;
            if (cmd->type != BASE_KCPU_COMMAND_TYPE_FENCE_SIGNAL ||
                fence->basep.fd != -1)
               failure = 1;
            fence->basep.fd = 20;
            fence_live = 1;
         }
         return 0;
      }
      enqueues++;
      if (enqueue->nr_commands != 1 || enqueue->id != 7)
         failure = 1;
      if ((scenario == 7 && enqueues == 1) ||
          (scenario == 8 && enqueues == 2) ||
          (scenario == 14 && enqueues == 3) ||
          (scenario == 31 && enqueues == 2)) {
         errno = ENOMEM;
         return -1;
      }
      if (enqueues == 1) {
         if (cqs_input_mode()) {
            struct base_cqs_wait_operation_info *wait =
               (void *)(uintptr_t)cmd->info.cqs_wait_operation.objs;
            uint32_t error;
            uint64_t value;
            memcpy(&value, (cached ? backing : cpu) + 128, 8);
            memcpy(&error, (cached ? backing : cpu) + 136, 4);
            if (cmd->type != BASE_KCPU_COMMAND_TYPE_CQS_WAIT_OPERATION ||
                cmd->info.cqs_wait_operation.nr_objs != 1 ||
                cmd->info.cqs_wait_operation.inherit_err_flags != 1 ||
                wait->addr != (uintptr_t)cpu + 128 || wait->val != 0 ||
                wait->operation != BASEP_CQS_WAIT_OPERATION_GT ||
                wait->data_type != BASEP_CQS_DATA_TYPE_U64 ||
                value != 0 || error != (scenario != 29))
               failure = 1;
         } else {
            struct base_fence *fence = (void *)(uintptr_t)cmd->info.fence.fence;
            if (cmd->type != BASE_KCPU_COMMAND_TYPE_FENCE_WAIT ||
                fence->basep.fd != 20 || status != 0)
               failure = 1;
         }
      } else {
         const unsigned char *obj = (void *)(uintptr_t)cmd->info.padding[0];
         uint64_t addr, val;
         memcpy(&addr, obj, 8);
         memcpy(&val, obj + 8, 8);
         if (cmd->type != BASE_KCPU_COMMAND_TYPE_CQS_SET_OPERATION ||
             cmd->info.padding[1] != 1 || val != 1 ||
             addr != (uintptr_t)cpu + (enqueues == 2 ? 0 : 64) ||
             obj[16] != 1 || obj[17] != BASEP_CQS_DATA_TYPE_U64)
            failure = 1;
      }
      publish();
   } else if (request == KBASE_IOCTL_KCPU_QUEUE_DELETE) {
      if (scenario >= 18 &&
          ((struct kbase_ioctl_kcpu_queue_delete *)data)->id == 8) {
         producer_deletes++;
         if (!producer_live || queue_live)
            failure = 1;
         if (scenario == 23) {
            errno = EIO;
            return -1;
         }
         producer_live = 0;
         status = 1;
         return 0;
      }
      deletes++;
      if (((struct kbase_ioctl_kcpu_queue_delete *)data)->id != 7)
         failure = 1;
      if (scenario == 9 || scenario == 33) {
         errno = EIO;
         return -1;
      }
      if (enqueues == 3) {
         int old_status = status;
         status = 1;
         publish();
         if (scenario == 3 || scenario >= 18)
            status = old_status;
      }
      queue_live = 0;
   } else {
      abort();
   }
   return 0;
}

static void *mock_mmap(void *addr, size_t size, int prot, int flags,
                       int fd, off_t offset)
{
   (void)addr; (void)size; (void)prot; (void)flags; (void)fd;
   return offset == BASE_MEM_MAP_TRACKING_HANDLE ? tracking : cpu;
}
static int mock_munmap(void *addr, size_t size)
{
   (void)size;
   if (addr == cpu) {
      event_unmaps++;
      if (queue_live || producer_live)
         failure = 1;
   }
   return 0;
}
static long mock_sysconf(int name)
{
   (void)name;
   return scenario == 15 ? 16384 : 4096;
}
static int mock_clock_gettime(clockid_t clock, struct timespec *time)
{
   (void)clock;
   ticks++;
   publish();
   time->tv_sec = ticks / 1000;
   time->tv_nsec = (ticks % 1000) * 1000000;
   return 0;
}
static int mock_nanosleep(const struct timespec *time, struct timespec *remaining)
{
   (void)time; (void)remaining;
   return 0;
}

#define open mock_open
#define close mock_close
#define ioctl mock_ioctl
#define mmap mock_mmap
#define munmap mock_munmap
#define sysconf mock_sysconf
#define clock_gettime mock_clock_gettime
#define nanosleep mock_nanosleep
#define main native_main
#include "sync/kcpu_fence_wait_test.c"
#undef main

int main(int argc, char **argv)
{
   if (argc != 2)
      return 99;
   scenario = atoi(argv[1]);
   char *args[] = {"native-test", "/mock/timeline",
                  scenario == 3 ? "pending-delete" :
                  (scenario == 2 || scenario == 6 || scenario == 13 ?
                   "error" : "success"), "--cached", NULL};
   if (scenario >= 18) {
      args[1] = "--kcpu";
      args[2] = scenario == 19 ? "pending-delete" :
                scenario == 20 ? "error" : "success";
   }
   if (cqs_input_mode()) {
      args[1] = "--kcpu-cqs";
      args[2] = scenario == 29 ? "success" : "error";
   }
   int result = native_main(scenario == 2 || scenario == 11 || scenario == 17 ?
                            4 : (scenario == 18 || scenario == 24 ||
                                 scenario == 30 ? 4 : 3), args);
   if (timeline_live || fence_live)
      failure = 1;
   if ((scenario == 4 || scenario == 5 || scenario == 6 || scenario == 15) &&
       mali_opens != 0)
      failure = 1;
   if (scenario == 20 && (mali_opens || timeline_live || creates))
      failure = 1;
   if ((scenario == 9 || scenario == 23 || scenario == 33) &&
       (event_unmaps || mali_closes))
      failure = 1;
   if (scenario != 9 && scenario != 23 && scenario != 33 &&
       mali_opens && mali_closes != 1)
      failure = 1;
   if (scenario >= 18 && scenario != 20 && !cqs_input_mode() &&
       (producer_deletes != 1 || (producer_live && scenario != 23)))
      failure = 1;
   if ((scenario == 7 || scenario == 8 || scenario == 14 || scenario == 31 ||
        scenario == 32 || scenario == 33) && deletes != 1)
      failure = 1;
   if (failure) {
      fprintf(stderr, "FAIL mock lifecycle/protocol invariant\n");
      return 99;
   }
   return result;
}
"""


class NativeKCPUFenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="kcpu-native-offline-")
        cls.addClassCleanup(cls.tmp.cleanup)
        fixture = Path(cls.tmp.name) / "fixture.c"
        fixture.write_text(MOCK)
        cls.binary = Path(cls.tmp.name) / "fixture"
        subprocess.run(
            ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
             "-Wno-unused-function",
             "-I", str(ROOT / "tests"),
             "-I", str(ROOT / "patches/kbase-common/files/include"),
             str(fixture), "-o", str(cls.binary)],
            check=True, capture_output=True, text=True,
        )

    def run_case(self, scenario, expected, message):
        result = subprocess.run(
            [str(self.binary), str(scenario)],
            capture_output=True, text=True, timeout=5,
        )
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, expected, output)
        self.assertIn(message, output)

    def test_pending_success_publishes_payload_before_done(self):
        self.run_case(1, 0, "PASS KCPU_PUBLISH success")

    def test_negative_fence_refreshes_cached_payload_after_done(self):
        self.run_case(2, 0, "PASS KCPU_PUBLISH error")

    def test_delete_drains_but_does_not_signal_pending_fence(self):
        self.run_case(3, 0, "PASS KCPU_DELETE_DRAIN")

    def test_missing_or_inaccessible_provider_blocks_before_mali(self):
        for scenario in (4, 5):
            with self.subTest(scenario=scenario):
                self.run_case(scenario, 77, "BLOCKED sw_sync")

    def test_provider_without_negative_close_blocks_before_mali(self):
        self.run_case(6, 77, "BLOCKED sw_sync negative")

    def test_each_enqueue_failure_deletes_before_unmapping(self):
        for scenario in (7, 8, 14):
            with self.subTest(scenario=scenario):
                self.run_case(scenario, 1, "FAIL KCPU ENQUEUE")

    def test_failed_delete_retains_mapping_and_context(self):
        self.run_case(9, 1, "FATAL KCPU DELETE")

    def test_unverified_uapi_and_page_size_are_blocked(self):
        for scenario, message in ((10, "BLOCKED CSF UAPI"),
                                  (15, "BLOCKED page size")):
            with self.subTest(scenario=scenario):
                self.run_case(scenario, 77, message)

    def test_cached_request_cannot_pass_as_uncached(self):
        self.run_case(11, 77, "BLOCKED cached")

    def test_publication_timeout_fails_and_cleans_up(self):
        self.run_case(12, 1, "FAIL KCPU publication timeout")

    def test_negative_fence_without_payload_error_fails(self):
        self.run_case(13, 1, "FAIL KCPU payload")

    def test_publication_while_fence_pending_fails(self):
        self.run_case(16, 1, "FAIL KCPU published while fence pending")

    def test_system_coherent_memory_does_not_issue_mem_sync(self):
        self.run_case(17, 0, "PASS KCPU_PUBLISH success")

    def test_kcpu_producer_cached_success_uses_distinct_queue_and_cell(self):
        self.run_case(18, 0, "PASS KCPU_PUBLISH success")

    def test_kcpu_pending_delete_does_not_release_producer(self):
        self.run_case(19, 0, "PASS KCPU_DELETE_DRAIN")

    def test_kcpu_error_mode_blocks_before_opening_mali(self):
        self.run_case(20, 77, "BLOCKED KCPU producer cannot create a negative fence")

    def test_kcpu_producer_partial_enqueue_failure_cleans_up(self):
        for scenario in (21, 22):
            with self.subTest(scenario=scenario):
                self.run_case(scenario, 1, "FAIL producer KCPU ENQUEUE")

    def test_kcpu_producer_delete_failure_retains_event_mapping(self):
        self.run_case(23, 1, "FATAL KCPU DELETE")

    def test_kcpu_producer_release_failures_clean_up_both_queues(self):
        for scenario, message in ((24, "FAIL producer MEM_SYNC"),
                                  (25, "FAIL producer CS_EVENT_SIGNAL")):
            with self.subTest(scenario=scenario):
                self.run_case(scenario, 1, message)

    def test_kcpu_producer_status_wait_is_bounded_and_rejects_error(self):
        for scenario, message in ((26, "FAIL producer fence timeout"),
                                  (27, "FAIL producer fence status")):
            with self.subTest(scenario=scenario):
                self.run_case(scenario, 1, message)

    def test_cqs_input_error_is_inherited_and_published(self):
        for scenario in (28, 30):
            with self.subTest(scenario=scenario):
                self.run_case(scenario, 0, "PASS KCPU_CQS_INHERIT error")

    def test_cqs_input_without_error_is_success_control(self):
        self.run_case(29, 0, "PASS KCPU_CQS_INHERIT success")

    def test_cqs_input_failures_keep_resources_until_delete(self):
        for scenario, message in ((31, "FAIL KCPU ENQUEUE"),
                                  (32, "FAIL producer CS_EVENT_SIGNAL"),
                                  (33, "FATAL KCPU DELETE")):
            with self.subTest(scenario=scenario):
                self.run_case(scenario, 1, message)


if __name__ == "__main__":
    unittest.main()
