#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <linux/sync_file.h>
#include <stddef.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

#include "drm-uapi/mali_kbase_ioctl.h"

struct sw_sync_create_fence_data {
   uint32_t value;
   char name[32];
   int32_t fence;
};
#define SW_SYNC_IOC_CREATE_FENCE \
   _IOWR('W', 0, struct sw_sync_create_fence_data)
#define SW_SYNC_IOC_INC _IOW('W', 1, uint32_t)

/* Draft 006's SET payload is not in the selected base header yet. */
struct cqs_set_object {
   uint64_t addr, val;
   uint8_t operation, data_type, padding[6];
};
struct cqs_set_payload {
   uint64_t objs;
   uint32_t nr_objs, padding;
};
struct event_cell {
   volatile uint64_t value;
   volatile uint32_t error;
   uint8_t padding[52];
};
_Static_assert(sizeof(struct cqs_set_object) == 24, "CQS SET object ABI");
_Static_assert(sizeof(struct cqs_set_payload) == 16, "CQS SET payload ABI");
_Static_assert(sizeof(struct base_kcpu_command) == 24, "KCPU command ABI");
_Static_assert(sizeof(struct event_cell) == 64, "distinct event slots");
_Static_assert(offsetof(struct event_cell, error) == 8, "U64 event error ABI");

struct producer {
   int timeline, fence;
   uint8_t queue;
   bool queue_created;
};

static int
check_fd(int fd, int expected, const char *stage)
{
   struct sync_file_info info = {0};
   if (ioctl(fd, SYNC_IOC_FILE_INFO, &info)) {
      fprintf(stderr, "FAIL %s SYNC_IOC_FILE_INFO: %s\n", stage, strerror(errno));
      return 1;
   }
   printf("INFO %s sync_file status=%d\n", stage, info.status);
   if ((expected < 0 && info.status >= 0) ||
       (expected >= 0 && info.status != expected)) {
      fprintf(stderr, "%s %s status=%d expected=%d\n",
              expected < 0 ? "BLOCKED" : "FAIL", stage, info.status, expected);
      return expected < 0 ? 77 : 1;
   }
   return 0;
}

static int
close_timeline(struct producer *producer)
{
   int fd = producer->timeline;
   producer->timeline = -1;
   if (fd >= 0 && close(fd)) {
      fprintf(stderr, "FAIL sw_sync close timeline: %s\n", strerror(errno));
      return 1;
   }
   return 0;
}

static int
close_producer(struct producer *producer)
{
   int result = close_timeline(producer);
   int fd = producer->fence;
   producer->fence = -1;
   if (fd >= 0 && close(fd)) {
      fprintf(stderr, "FAIL sw_sync close fence: %s\n", strerror(errno));
      result = 1;
   }
   return result;
}

static int
open_producer(struct producer *producer, const char *path)
{
   producer->timeline = open(path, O_RDWR | O_CLOEXEC);
   if (producer->timeline < 0) {
      int error = errno;
      bool unavailable = error == ENOENT || error == EACCES || error == EPERM;
      fprintf(stderr, "%s sw_sync open %s: %s\n",
              unavailable ? "BLOCKED" : "FAIL", path, strerror(error));
      return unavailable ? 77 : 1;
   }
   struct sw_sync_create_fence_data create = {.value = 1, .fence = -1};
   memcpy(create.name, "kcpu-native", sizeof("kcpu-native"));
   if (ioctl(producer->timeline, SW_SYNC_IOC_CREATE_FENCE, &create)) {
      int error = errno;
      fprintf(stderr, "%s sw_sync CREATE_FENCE: %s\n",
              error == ENOTTY ? "BLOCKED" : "FAIL", strerror(error));
      return error == ENOTTY ? 77 : 1;
   }
   producer->fence = create.fence;
   return check_fd(producer->fence, 0, "sw_sync pending");
}

static int
cache_sync(int mali, struct event_cell *cells, bool needs_sync, uint8_t type)
{
   if (!needs_sync)
      return 0;
   struct kbase_ioctl_mem_sync sync = {
      .handle = (uintptr_t)cells, .user_addr = (uintptr_t)cells,
      .size = 2 * sizeof(*cells), .type = type,
   };
   if (ioctl(mali, KBASE_IOCTL_MEM_SYNC, &sync)) {
      fprintf(stderr, "FAIL MEM_SYNC type=%u: %s\n", type, strerror(errno));
      return 1;
   }
   return 0;
}

static int
milliseconds(uint64_t *value)
{
   struct timespec now;
   if (clock_gettime(CLOCK_MONOTONIC, &now)) {
      fprintf(stderr, "FAIL clock_gettime: %s\n", strerror(errno));
      return 1;
   }
   *value = (uint64_t)now.tv_sec * 1000 + now.tv_nsec / 1000000;
   return 0;
}

static int
sleep_tick(void)
{
   const struct timespec delay = {.tv_nsec = 1000000};
   if (nanosleep(&delay, NULL) && errno != EINTR) {
      fprintf(stderr, "FAIL nanosleep: %s\n", strerror(errno));
      return 1;
   }
   return 0;
}

static int
hold_pending(int mali, struct event_cell *cells, bool needs_sync)
{
   uint64_t start, now;
   if (milliseconds(&start))
      return 1;
   for (;;) {
      if (cache_sync(mali, cells, needs_sync, BASE_SYNCSET_OP_CSYNC))
         return 1;
      if (cells[0].value || cells[1].value || cells[0].error || cells[1].error) {
         fprintf(stderr, "FAIL KCPU published while fence pending\n");
         return 1;
      }
      if (milliseconds(&now))
         return 1;
      if (now - start >= 20)
         return 0;
      if (sleep_tick())
         return 1;
   }
}

static int
wait_publication(int mali, struct event_cell *cells, bool needs_sync)
{
   uint64_t start, now;
   if (milliseconds(&start))
      return 1;
   for (;;) {
      if (cache_sync(mali, cells, needs_sync, BASE_SYNCSET_OP_CSYNC))
         return 1;
      if (cells[1].value >= 1) {
         atomic_thread_fence(memory_order_acquire);
         /* Read A only after observing B, with a fresh CPU invalidation. */
         return cache_sync(mali, cells, needs_sync, BASE_SYNCSET_OP_CSYNC);
      }
      if (milliseconds(&now))
         return 1;
      if (now - start >= 2000) {
         fprintf(stderr, "FAIL KCPU publication timeout (2000 ms)\n");
         return 1;
      }
      if (sleep_tick())
         return 1;
   }
}

static int
delete_queue(int mali, uint8_t id)
{
   struct kbase_ioctl_kcpu_queue_delete deletion = {.id = id};
   if (ioctl(mali, KBASE_IOCTL_KCPU_QUEUE_DELETE, &deletion)) {
      fprintf(stderr, "FATAL KCPU DELETE: %s; retain event mapping and context "
                      "until process exit, no explicit BO release\n", strerror(errno));
      return 1;
   }
   return 0;
}

static int
sync_producer_cell(int mali, struct event_cell *cells, bool needs_sync)
{
   if (!needs_sync)
      return 0;
   struct kbase_ioctl_mem_sync sync = {
      .handle = (uintptr_t)cells, .user_addr = (uintptr_t)&cells[2],
      .size = sizeof(cells[2]), .type = BASE_SYNCSET_OP_MSYNC,
   };
   if (ioctl(mali, KBASE_IOCTL_MEM_SYNC, &sync)) {
      fprintf(stderr, "FAIL producer MEM_SYNC: %s\n", strerror(errno));
      return 1;
   }
   return 0;
}

static int
open_kcpu_producer(int mali, struct event_cell *cells, bool needs_sync,
                   struct producer *producer)
{
   if (sync_producer_cell(mali, cells, needs_sync))
      return 1;
   struct kbase_ioctl_kcpu_queue_new queue = {0};
   if (ioctl(mali, KBASE_IOCTL_KCPU_QUEUE_CREATE, &queue)) {
      fprintf(stderr, "FAIL producer KCPU CREATE: %s\n", strerror(errno));
      return 1;
   }
   producer->queue = queue.id;
   producer->queue_created = true;
   struct base_cqs_wait_operation_info wait = {
      .addr = (uintptr_t)&cells[2], .val = 0,
      .operation = BASEP_CQS_WAIT_OPERATION_GT,
      .data_type = BASEP_CQS_DATA_TYPE_U64,
   };
   struct base_fence fence = {.basep = {.fd = -1, .stream_fd = -1}};
   struct base_kcpu_command commands[] = {
      {.type = BASE_KCPU_COMMAND_TYPE_CQS_WAIT_OPERATION,
       .info.cqs_wait_operation = {.objs = (uintptr_t)&wait, .nr_objs = 1}},
      {.type = BASE_KCPU_COMMAND_TYPE_FENCE_SIGNAL,
       .info.fence = {.fence = (uintptr_t)&fence}},
   };
   for (unsigned i = 0; i < 2; i++) {
      struct kbase_ioctl_kcpu_queue_enqueue enqueue = {
         .addr = (uintptr_t)&commands[i], .nr_commands = 1, .id = queue.id,
      };
      int ret = ioctl(mali, KBASE_IOCTL_KCPU_QUEUE_ENQUEUE, &enqueue);
      producer->fence = fence.basep.fd;
      if (ret) {
         fprintf(stderr, "FAIL producer KCPU ENQUEUE %u/2: %s; accepted=%u\n",
                 i + 1, strerror(errno), i);
         return 1;
      }
   }
   return check_fd(producer->fence, 0, "KCPU producer pending");
}

static int
release_kcpu_producer(int mali, struct event_cell *cells, bool needs_sync,
                      struct producer *producer)
{
   __atomic_store_n(&cells[2].value, 1, __ATOMIC_RELEASE);
   if (sync_producer_cell(mali, cells, needs_sync))
      return 1;
   if (ioctl(mali, KBASE_IOCTL_CS_EVENT_SIGNAL)) {
      fprintf(stderr, "FAIL producer CS_EVENT_SIGNAL: %s\n", strerror(errno));
      return 1;
   }
   uint64_t start, now;
   if (milliseconds(&start))
      return 1;
   for (;;) {
      struct sync_file_info info = {0};
      if (ioctl(producer->fence, SYNC_IOC_FILE_INFO, &info)) {
         fprintf(stderr, "FAIL producer SYNC_IOC_FILE_INFO: %s\n", strerror(errno));
         return 1;
      }
      if (info.status == 1)
         return 0;
      if (info.status != 0) {
         fprintf(stderr, "FAIL producer fence status=%d expected=1\n", info.status);
         return 1;
      }
      if (milliseconds(&now))
         return 1;
      if (now - start >= 2000) {
         fprintf(stderr, "FAIL producer fence timeout (2000 ms)\n");
         return 1;
      }
      if (sleep_tick())
         return 1;
   }
}

int
main(int argc, char **argv)
{
   if ((argc != 3 && argc != 4) ||
       (argc == 4 && strcmp(argv[3], "--cached")) ||
       (strcmp(argv[2], "success") && strcmp(argv[2], "error") &&
        strcmp(argv[2], "pending-delete"))) {
      fprintf(stderr, "usage: %s <sw_sync-path|--kcpu> "
                      "<success|error|pending-delete> [--cached]\n", argv[0]);
      return 2;
   }
   setvbuf(stdout, NULL, _IONBF, 0);
   printf("GPU_GUARD=NOT_EXECUTED PANVK_COMPLETION=NOT_EXECUTED "
          "CSF_TERMINATION=NOT_EXECUTED\n");
   long page_size = sysconf(_SC_PAGESIZE);
   if (page_size != 4096 || sizeof(void *) != 8) {
      fprintf(stderr, "BLOCKED page size/ABI: page=%ld pointer=%zu; "
                      "requires 4 KiB and 64-bit\n", page_size, sizeof(void *));
      return 77;
   }

   const bool error_case = !strcmp(argv[2], "error");
   const bool kcpu_producer = !strcmp(argv[1], "--kcpu");
   if (kcpu_producer && error_case) {
      fprintf(stderr, "BLOCKED KCPU producer cannot create a negative fence; "
                      "error gate remains untested\n");
      return 77;
   }
   printf("INFO producer=%s\n", kcpu_producer ? "kcpu" : "sw_sync");
   const bool delete_pending = !strcmp(argv[2], "pending-delete");
   const bool request_cached = argc == 4;
   struct producer producer = {.timeline = -1, .fence = -1};
   int mali = -1, result = 1;
   void *tracking = MAP_FAILED;
   struct event_cell *cells = MAP_FAILED;
   bool queue_created = false, needs_sync = false;
   struct kbase_ioctl_kcpu_queue_new queue = {0};

   if (!kcpu_producer) {
      result = open_producer(&producer, argv[1]);
      if (result)
         goto cleanup;
      if (error_case) {
         result = close_timeline(&producer);
         if (!result)
            result = check_fd(producer.fence, -1, "sw_sync negative preflight");
         if (close_producer(&producer))
            result = 1;
         if (result)
            goto cleanup;
         result = open_producer(&producer, argv[1]);
         if (result)
            goto cleanup;
      }
   }

   result = 1;
   mali = open("/dev/mali0", O_RDWR | O_CLOEXEC);
   if (mali < 0) {
      int error = errno;
      result = error == ENOENT || error == EACCES || error == EPERM ? 77 : 1;
      fprintf(stderr, "%s Mali open: %s\n", result == 77 ? "BLOCKED" : "FAIL",
              strerror(error));
      goto cleanup;
   }
   struct kbase_ioctl_version_check version = {0};
   if (ioctl(mali, KBASE_IOCTL_VERSION_CHECK_CSF, &version)) {
      fprintf(stderr, "FAIL VERSION_CHECK_CSF: %s\n", strerror(errno));
      goto cleanup;
   }
   printf("INFO CSF UAPI %u.%u\n", version.major, version.minor);
   if (version.major != 1 || version.minor != 21) {
      fprintf(stderr, "BLOCKED CSF UAPI: this harness requires verified 1.21\n");
      result = 77;
      goto cleanup;
   }
   struct kbase_ioctl_set_flags flags = {0};
   if (ioctl(mali, KBASE_IOCTL_SET_FLAGS, &flags)) {
      fprintf(stderr, "FAIL SET_FLAGS: %s\n", strerror(errno));
      goto cleanup;
   }
   tracking = mmap(NULL, 4096, PROT_NONE, MAP_SHARED, mali,
                   BASE_MEM_MAP_TRACKING_HANDLE);
   if (tracking == MAP_FAILED) {
      fprintf(stderr, "FAIL tracking mmap: %s\n", strerror(errno));
      goto cleanup;
   }
   union kbase_ioctl_mem_alloc_ex alloc = {.in = {
      .va_pages = 1, .commit_pages = 1,
      .flags = BASE_MEM_PROT_CPU_RD | BASE_MEM_PROT_CPU_WR |
               BASE_MEM_PROT_GPU_RD | BASE_MEM_PROT_GPU_WR |
               BASE_MEM_SAME_VA | BASE_MEM_CSF_EVENT |
               (request_cached ? BASE_MEM_CACHED_CPU : 0),
   }};
   if (ioctl(mali, KBASE_IOCTL_MEM_ALLOC_EX, &alloc)) {
      fprintf(stderr, "FAIL MEM_ALLOC_EX: %s\n", strerror(errno));
      goto cleanup;
   }
   if (!(alloc.out.flags & BASE_MEM_SAME_VA) ||
       !(alloc.out.flags & BASE_MEM_CSF_EVENT)) {
      fprintf(stderr, "BLOCKED event allocation is not SAME_VA/CSF_EVENT\n");
      result = 77;
      goto cleanup;
   }
   const bool cached = !!(alloc.out.flags & BASE_MEM_CACHED_CPU);
   needs_sync = cached && !(alloc.out.flags & BASE_MEM_COHERENT_SYSTEM);
   if (request_cached && !cached) {
      fprintf(stderr, "BLOCKED cached request returned an uncached allocation\n");
      result = 77;
      goto cleanup;
   }
   printf("INFO event flags=%#" PRIx64 " cached_cpu=%u mem_sync=%u\n",
          (uint64_t)alloc.out.flags, cached, needs_sync);
   cells = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED,
                mali, alloc.out.gpu_va);
   if (cells == MAP_FAILED) {
      fprintf(stderr, "FAIL event mmap: %s\n", strerror(errno));
      goto cleanup;
   }
   memset(cells, 0, 4096);
   if (cache_sync(mali, cells, needs_sync, BASE_SYNCSET_OP_MSYNC))
      goto cleanup;
   if (kcpu_producer && open_kcpu_producer(mali, cells, needs_sync, &producer))
      goto cleanup;
   if (ioctl(mali, KBASE_IOCTL_KCPU_QUEUE_CREATE, &queue)) {
      fprintf(stderr, "FAIL KCPU CREATE: %s\n", strerror(errno));
      goto cleanup;
   }
   queue_created = true;
   struct base_fence fence = {.basep = {.fd = producer.fence, .stream_fd = -1}};
   struct cqs_set_object objects[2] = {
      {.addr = (uintptr_t)&cells[0], .val = 1, .operation = 1,
       .data_type = BASEP_CQS_DATA_TYPE_U64},
      {.addr = (uintptr_t)&cells[1], .val = 1, .operation = 1,
       .data_type = BASEP_CQS_DATA_TYPE_U64},
   };
   struct base_kcpu_command commands[3] = {
      {.type = BASE_KCPU_COMMAND_TYPE_FENCE_WAIT,
       .info.fence = {.fence = (uintptr_t)&fence}},
      {.type = BASE_KCPU_COMMAND_TYPE_CQS_SET_OPERATION},
      {.type = BASE_KCPU_COMMAND_TYPE_CQS_SET_OPERATION},
   };
   for (unsigned i = 0; i < 2; i++) {
      const struct cqs_set_payload payload = {
         .objs = (uintptr_t)&objects[i], .nr_objs = 1,
      };
      memcpy(&commands[i + 1].info, &payload, sizeof(payload));
   }
   for (unsigned i = 0; i < 3; i++) {
      struct kbase_ioctl_kcpu_queue_enqueue enqueue = {
         .addr = (uintptr_t)&commands[i], .nr_commands = 1, .id = queue.id,
      };
      if (ioctl(mali, KBASE_IOCTL_KCPU_QUEUE_ENQUEUE, &enqueue)) {
         fprintf(stderr, "FAIL KCPU ENQUEUE %u/3: %s; accepted=%u\n",
                 i + 1, strerror(errno), i);
         goto cleanup;
      }
   }
   if (hold_pending(mali, cells, needs_sync) ||
       check_fd(producer.fence, 0, "KCPU fence held 20 ms"))
      goto cleanup;
   if (delete_pending) {
      if (delete_queue(mali, queue.id))
         goto retain;
      queue_created = false;
      if (wait_publication(mali, cells, needs_sync) ||
          check_fd(producer.fence, 0, "DELETE leaves fence pending"))
         goto cleanup;
      if (cells[0].value != 1 || cells[1].value != 1) {
         fprintf(stderr, "FAIL DELETE did not drain both SET commands\n");
         goto cleanup;
      }
      printf("PASS KCPU_DELETE_DRAIN (not successful dependency completion)\n");
   } else {
      if (kcpu_producer) {
         if (release_kcpu_producer(mali, cells, needs_sync, &producer))
            goto cleanup;
      } else if (error_case) {
         if (close_timeline(&producer))
            goto cleanup;
      } else {
         uint32_t increment = 1;
         if (ioctl(producer.timeline, SW_SYNC_IOC_INC, &increment)) {
            fprintf(stderr, "FAIL sw_sync INC: %s\n", strerror(errno));
            goto cleanup;
         }
      }
      result = check_fd(producer.fence, error_case ? -1 : 1, "producer release");
      if (result)
         goto cleanup;
      result = 1;
      if (wait_publication(mali, cells, needs_sync))
         goto cleanup;
      if (cells[0].value != 1 || cells[1].value != 1 ||
          !!cells[0].error != error_case) {
         fprintf(stderr, "FAIL KCPU payload A=%" PRIu64 " B=%" PRIu64
                         " A.error=%u expected_error=%u\n",
                 cells[0].value, cells[1].value, cells[0].error, error_case);
         goto cleanup;
      }
      printf("PASS KCPU_PUBLISH %s A=%" PRIu64 " B=%" PRIu64 " A.error=%u\n",
             argv[2], cells[0].value, cells[1].value, cells[0].error);
   }
   result = 0;

cleanup:
   if (queue_created && delete_queue(mali, queue.id))
      goto retain;
   if (producer.queue_created && delete_queue(mali, producer.queue))
      goto retain;
   if (close_producer(&producer))
      result = 1;
   /* SAME_VA mappings are free-on-close: no MEM_FREE after munmap. */
   if (cells != MAP_FAILED && munmap(cells, 4096)) {
      fprintf(stderr, "FAIL event munmap: %s\n", strerror(errno));
      result = 1;
   }
   if (tracking != MAP_FAILED && munmap(tracking, 4096)) {
      fprintf(stderr, "FAIL tracking munmap: %s\n", strerror(errno));
      result = 1;
   }
   if (mali >= 0 && close(mali)) {
      fprintf(stderr, "FAIL Mali close: %s\n", strerror(errno));
      result = 1;
   }
   return result;

retain:
   close_producer(&producer);
   return 1;
}
