"""Compile bridge/snapshot code and opt-in prepared PanVK source with stubs.

PANVK_KBASE_TEST_MESA selects a read-only prepared Mesa tree for integration
RED tests. The command interpreter models builder calls, not ISA encoding,
CPU/GPU visibility, kernel termination, or physical-device execution.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches/experimental-kbase-sync/006-kbase-kcpu-gpu-fence-wait.patch"
UAPI = "include/drm-uapi/mali_kbase_ioctl.h"
HEADER = "src/panfrost/lib/kmod/kbase_kmod.h"
SOURCE = "src/panfrost/lib/kmod/kbase_kmod.c"
PHYSICAL_DEVICE = "src/panfrost/vulkan/panvk_physical_device.c"
GPU_QUEUE = "src/panfrost/vulkan/csf/panvk_vX_gpu_queue.c"


def patch_hunks(path):
    if not PATCH.exists():
        return []
    hunks = []
    current = None
    selected = False
    for line in PATCH.read_text().splitlines():
        if line.startswith("diff --git "):
            selected = line == f"diff --git a/{path} b/{path}"
            current = None
        elif selected and line.startswith("@@ "):
            current = []
            hunks.append(current)
        elif selected and current is not None and line.startswith((" ", "+", "-")):
            current.append(line)
        elif selected and current is not None and not line:
            current.append(" ")
    return hunks


def added_code(path, containing=None):
    hunks = patch_hunks(path)
    if containing is not None:
        hunks = [hunk for hunk in hunks
                 if any(containing in line for line in hunk)]
        if len(hunks) != 1:
            raise AssertionError(f"Expected one patch hunk containing {containing}")
    return "\n".join(line[1:] for hunk in hunks
                     for line in hunk if line.startswith("+"))


def patched_uapi():
    text = (ROOT / "patches/kbase-common/files" / UAPI).read_text()
    for hunk in patch_hunks(UAPI):
        old = "\n".join(line[1:] for line in hunk if line.startswith((" ", "-"))) + "\n"
        new = "\n".join(line[1:] for line in hunk if line.startswith((" ", "+"))) + "\n"
        if text.count(old) != 1:
            raise AssertionError("UAPI patch context does not match the overlay")
        text = text.replace(old, new, 1)
    return text


def snapshot_function():
    text = added_code(PHYSICAL_DEVICE)
    name = "panvk_kbase_sync_dup_sync_file_fd"
    start = text.find(name + "(")
    if start < 0:
        raise AssertionError(f"Task 3 snapshot implementation missing from 006: {name}")
    end = text.find("\n}", start)
    if end < 0:
        raise AssertionError(f"Task 3 snapshot function is incomplete: {name}")
    return "VkResult\n" + text[start:end + 2]


def prepared_function(text, name):
    match = re.search(
        r"\n(?:static )?(VkResult|void|int|bool)\n" + re.escape(name) +
        r"\([^;{}]*\)\n\{", text)
    if not match:
        raise AssertionError(f"Prepared function is missing: {name}")
    end = text.find("\n}", match.end())
    if end < 0:
        raise AssertionError(f"Prepared function is incomplete: {name}")
    return "static " + text[match.start() + 1:end + 2].removeprefix("static ")


@unittest.skipUnless(os.environ.get("PANVK_KBASE_TEST_MESA"),
                     "PANVK_KBASE_TEST_MESA must select a prepared read-only Mesa tree")
class CheckedFenceTeardownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        mesa = Path(os.environ["PANVK_KBASE_TEST_MESA"]).resolve()
        revision = subprocess.run(
            ["git", "-C", str(mesa), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5, check=True)
        expected = json.loads((ROOT / "sources.lock").read_text())["mesaCommit"]
        if revision.stdout.strip() != expected:
            raise AssertionError("Teardown fixture must use the pinned Mesa revision")
        kmod = (mesa / SOURCE).read_text()
        queue = (mesa / GPU_QUEUE).read_text()
        functions = [
            prepared_function(kmod, "kbase_kmod_csf_group_destroy"),
            prepared_function(kmod, "kbase_kmod_csf_queue_term"),
            prepared_function(queue, "kbase_destroy_group"),
            prepared_function(queue, "kbase_finish_failed_teardown"),
            prepared_function(queue, "kbase_finish_fence_import_and_seqnos"),
            prepared_function(queue, "cleanup_queue"),
            prepared_function(queue, "init_queue"),
            prepared_function(queue, "panvk_per_arch(create_gpu_queue)"),
            prepared_function(queue, "panvk_per_arch(destroy_gpu_queue)"),
        ]
        cls.temp = tempfile.TemporaryDirectory(prefix="checked-fence-teardown-")
        cls.addClassCleanup(cls.temp.cleanup)
        directory = Path(cls.temp.name)
        cls.exe = directory / "teardown"
        source = directory / "teardown.c"
        source.write_text(r"""
#include <assert.h>
#include <errno.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <string.h>
#include "drm-uapi/mali_kbase_ioctl.h"
#define HAVE_PAN_KMOD_KBASE 1
#define PANVK_SUBQUEUE_COUNT 3
#define panvk_per_arch(name) name
#define container_of(ptr, type, field) \
   ((type *)((char *)(ptr) - offsetof(type, field)))
#define VK_SUCCESS 0
#define VK_ERROR_OUT_OF_HOST_MEMORY (-1)
#define VK_ERROR_OUT_OF_DEVICE_MEMORY (-2)
#define VK_ERROR_INITIALIZATION_FAILED (-3)
#define VK_SYSTEM_ALLOCATION_SCOPE_DEVICE 0
#define DEVICE_QUEUE_SHADER_CORE_CONTROL_CREATE_INFO_ARM 0
#define PANVK_DEBUG(flag) 0
#define static_assert _Static_assert
#define PAN_KMOD_BO_FLAG_CSF_EVENT 1
#define PANVK_QUEUE_TESS_READY_SYNC_OFFSET 48
#define PANVK_QUEUE_TESS_FREE_SYNC_OFFSET 56
#define PANVK_QUEUE_TESS_READY2_SYNC_OFFSET 52
#define PANVK_QUEUE_TESS_FREE2_SYNC_OFFSET 60
#define PANVK_QUEUE_DESC_RINGBUF_SYNC_OFFSET 80
#define PANVK_QUEUE_SYNCOBJS_SIZE 128
#define RENDER_DESC_RINGBUF_SIZE 128
typedef int VkResult;
typedef struct { const void *pNext; } VkDeviceQueueCreateInfo;
typedef struct { unsigned shaderCoreCount; } VkDeviceQueueShaderCoreControlCreateInfoARM;
struct pan_kmod_bo { int unused; };
struct pan_kmod_dev { int fd; };
struct vk_device { int alloc; };
struct vk_queue {
   struct { struct vk_device *device; } base;
   void (*driver_submit)(void);
};
struct panvk_device {
   struct vk_device vk;
   struct { struct pan_kmod_dev *dev; } kmod;
   struct { int rw; } mempools;
   struct { void *decode_ctx; } debug;
};
struct panvk_priv_bo { int unused; };
struct panvk_priv_mem { uintptr_t bo; unsigned offset; };
struct panvk_pool_alloc_info { unsigned size, alignment; };
struct panvk_cs_sync64 { uint64_t seqno; uint32_t error, padding; };
struct panvk_cs_sync32 { uint32_t seqno; };
struct kbase_kmod_csf_fence_import_queue { int unused; };
struct panvk_subqueue {
   struct { void *user_io; uint64_t ringbuf_dev;
            uint32_t group_handle; struct pan_kmod_bo *ringbuf_bo; } kbase;
};
struct panvk_gpu_queue {
   struct vk_queue vk;
   struct panvk_subqueue subqueues[3];
   struct { struct pan_kmod_bo *bo; } kbase_seqnos;
   struct kbase_kmod_csf_fence_import_queue *kbase_import_queue;
   struct { void *sync; } utrace;
   struct panvk_priv_mem syncobjs;
   uint32_t syncobj_handle;
};
static struct pan_kmod_dev kmod = {.fd = 3};
static struct panvk_device device = {.kmod = {.dev = &kmod}};
static struct pan_kmod_bo event_bo, ring_bo;
static struct kbase_kmod_csf_fence_import_queue import_queue;
static struct panvk_gpu_queue *allocated;
static int scenario, logs, deletes, releases, unmaps, freed, finished, heaps, lost;
static bool ordinary_live;
static unsigned ordinary_cleanups;
static _Alignas(8) unsigned char sync_data[128];
static struct panvk_priv_bo sync_bo;
static unsigned live_groups, terms, trace[32], count;
static void record(unsigned value) { assert(count < 32); trace[count++] = value; }
static void mesa_loge(const char *fmt, ...)
{ (void)fmt; logs++; errno = EINVAL; }
static struct panvk_device *to_panvk_device(struct vk_device *vk)
{ return container_of(vk, struct panvk_device, vk); }
static bool gpu_queue_uses_kbase(void *dev) { (void)dev; return true; }
static uint64_t kbase_kmod_page_size(void) { return 4096; }
static int mock_ioctl(int fd, unsigned long request, ...)
{
   assert(fd == 3);
   va_list args; va_start(args, request); void *data = va_arg(args, void *); va_end(args);
   if (request == KBASE_IOCTL_CS_QUEUE_TERMINATE) {
      assert(data);
      record(1);
      if (scenario == 3 || scenario == 11 || scenario == 14) {
         errno = EACCES; return -1;
      }
      terms++;
   } else {
      assert(request == KBASE_IOCTL_CS_QUEUE_GROUP_TERMINATE);
      struct kbase_ioctl_cs_queue_group_term *term = data;
      record(2);
      if (scenario == 4 || scenario == 13 || scenario == 15) {
         errno = EBUSY; return -1;
      }
      live_groups &= ~(1u << (term->group_handle - 100));
   }
   return 0;
}
static int mock_munmap(void *addr, size_t size)
{
   assert(addr && size == 3 * 4096);
   record(3);
   if (scenario == 5) { errno = ENOMEM; return -1; }
   unmaps++; return 0;
}
#define ioctl mock_ioctl
#define munmap mock_munmap
static void pan_kmod_bo_put(struct pan_kmod_bo *bo)
{
   if (!bo) return;
   assert(bo == &event_bo || bo == &ring_bo);
   if (bo == &event_bo) {
      assert(!live_groups); record(6); releases++;
   }
}
static int kbase_kmod_csf_fence_import_queue_destroy(
   struct kbase_kmod_csf_fence_import_queue *q)
{
   assert(q == &import_queue && !live_groups);
   record(5); deletes++;
   if (scenario == 2 || scenario == 12) { errno = EIO; return -1; }
   return 0;
}
static void cleanup_tiler(void *q)
{ (void)q; assert(!live_groups); heaps++; record(4); }
static void finish_subqueue(void *q, unsigned i)
{ (void)q; (void)i; assert(!ordinary_live || !live_groups); }
static void vk_sync_destroy(void *dev, void *sync) { (void)dev; (void)sync; }
static void finish_render_desc_ringbuf(void *q)
{ (void)q; assert(!ordinary_live || !live_groups); }
static void panvk_pool_free_mem(void *mem)
{
   (void)mem;
   assert(!ordinary_live || !live_groups);
   if (ordinary_live) ordinary_cleanups++;
   ordinary_live = false;
}
static VkResult kbase_queue_wait_current(void *q, uint64_t timeout)
{ (void)q; (void)timeout; return scenario >= 3 && scenario <= 5 ? -4 : VK_SUCCESS; }
static void panvk_mem_report(void *dev, bool final) { (void)dev; (void)final; }
static void destroy_group(void *q) { (void)q; assert(false); }
static int pan_kmod_sync_create(void *dev, unsigned flags, uint32_t *handle)
{ (void)dev; (void)flags; (void)handle; assert(false); return 0; }
static void pan_kmod_sync_destroy(void *dev, uint32_t handle)
{ (void)dev; (void)handle; assert(false); }
static void vk_queue_finish(void *q) { (void)q; finished++; }
static int vk_queue_set_lost(void *q, const char *message, ...)
{ (void)q; (void)message; lost++; return -4; }
static void vk_free(void *alloc, void *q) { (void)alloc; (void)q; freed++; }
static void *vk_zalloc(void *alloc, size_t size, size_t align, int scope)
{ (void)alloc; (void)align; (void)scope; allocated = calloc(1, size); return allocated; }
static int panvk_error(void *dev, int result) { (void)dev; return result; }
static int panvk_errorf(void *dev, int result, const char *fmt, ...)
{ (void)dev; (void)fmt; return result; }
static int vk_queue_init(struct vk_queue *q, struct vk_device *dev,
                         const void *info, unsigned idx)
{ (void)info; (void)idx; q->base.device = dev; return 0; }
static void *vk_find_struct_const(const void *info, int kind)
{ (void)info; (void)kind; return NULL; }
static unsigned get_panthor_group_priority(const void *info) { (void)info; return 0; }
static int create_group(void *q, unsigned priority, unsigned cores)
{ (void)q; (void)priority; (void)cores; assert(false); return 0; }
static void gpu_queue_submit(void) {}
static void setup(struct panvk_gpu_queue *q, unsigned groups)
{
   q->vk.base.device = &device.vk;
   live_groups = (1u << groups) - 1;
   for (unsigned i = 0; i < 3; i++) {
      q->subqueues[i].kbase.group_handle = i < groups ? 100 + i : UINT32_MAX;
      if (i < groups) {
         q->subqueues[i].kbase.user_io = (void *)(uintptr_t)(4096 * (i + 1));
         q->subqueues[i].kbase.ringbuf_dev = 0x10000 + 4096 * i;
         q->subqueues[i].kbase.ringbuf_bo = &ring_bo;
      }
   }
}
static int kbase_create_group(struct panvk_gpu_queue *q)
{ setup(q, scenario == 8 || scenario == 13 ? 1 : 3);
  return scenario == 8 || scenario == 13 ? -2 : 0; }
static int init_tiler(void *q) { (void)q; return scenario == 7 ? -2 : 0; }
static int panvk_priv_bo_create(void *dev, unsigned size, unsigned flags,
                                int scope, const char *name,
                                struct panvk_priv_bo **out)
{ (void)dev; (void)size; (void)flags; (void)scope; (void)name;
  ordinary_live = true; *out = &sync_bo; return 0; }
static struct panvk_priv_mem panvk_pool_alloc_mem(
   void *pool, struct panvk_pool_alloc_info info)
{ (void)pool; (void)info; assert(false); return (struct panvk_priv_mem){0}; }
static bool panvk_priv_mem_check_alloc(struct panvk_priv_mem mem) { return mem.bo != 0; }
static void *priv_mem_pointer(struct panvk_priv_mem mem, unsigned offset)
{ assert(mem.bo && offset < sizeof(sync_data)); return sync_data + offset; }
#define panvk_priv_mem_write(mem, offset, type, name) \
   for (type *name = priv_mem_pointer(mem, offset); name; name = NULL)
static void kbase_clean_priv_mem(struct panvk_priv_mem mem, unsigned offset, unsigned size)
{ (void)mem; (void)offset; (void)size; }
static int kbase_init_seqnos(struct panvk_gpu_queue *q)
{
   q->kbase_seqnos.bo = &event_bo;
   q->kbase_import_queue = &import_queue;
   return 0;
}
static int init_render_desc_ringbuf(void *q) { (void)q; return 0; }
static int init_utrace(void *q) { (void)q; return 0; }
static int init_subqueue(void *q, unsigned i) { (void)q; (void)i; return 0; }
static int kbase_submit_init_subqueues(void *q) { (void)q; return -2; }
static void pandecode_next_frame(void *ctx) { (void)ctx; }
""" + "\n\n".join(functions) + r"""
int main(int argc, char **argv)
{
   assert(argc == 2); scenario = atoi(argv[1]);
   struct panvk_gpu_queue q = {0}, *subject = &q;
   setup(&q, 3); q.kbase_seqnos.bo = &event_bo; q.kbase_import_queue = &import_queue;
   ordinary_live = true;
   if (scenario == 14) {
      assert(kbase_kmod_csf_queue_term(&kmod, 0x10000,
                                     q.subqueues[0].kbase.user_io) == -1);
      assert(errno == EACCES && !unmaps); return 0;
   }
   if (scenario == 15) {
      assert(kbase_kmod_csf_group_destroy(&kmod, 100) == -1);
      assert(errno == EBUSY && live_groups); return 0;
   }
   if ((scenario >= 6 && scenario <= 8) || scenario >= 11) {
      struct vk_queue *out = NULL;
      VkDeviceQueueCreateInfo info = {0};
      ordinary_live = false;
      assert(create_gpu_queue(&device, &info, 0, &out) == -2);
      if (scenario >= 11) {
         assert(!out && logs && !freed && finished == 1 && lost == 1 && !releases);
         assert(scenario == 12 ? deletes == 1 : deletes == 0);
         if (scenario != 13) {
            assert(scenario == 12 ? !ordinary_live && ordinary_cleanups == 1
                                  : ordinary_live && !ordinary_cleanups);
            assert(allocated->kbase_import_queue == &import_queue);
            assert(allocated->kbase_seqnos.bo == &event_bo);
         } else {
            assert(allocated->subqueues[0].kbase.ringbuf_bo == &ring_bo);
         }
         free(allocated); return 0;
      }
      assert(!out && freed == 1 && finished == 1 && !live_groups);
      assert(heaps == (scenario == 7 || scenario == 8 ? 0 : 1));
      assert(deletes == (scenario == 6 ? 1 : 0));
      assert(releases == (scenario == 6 ? 1 : 0));
      assert(!ordinary_live && ordinary_cleanups == (scenario == 6 ? 1 : 0));
      free(allocated); return 0;
   }
   if (scenario == 9) q.kbase_import_queue = NULL;
   if (scenario == 10) {
      live_groups = 0;
      cleanup_queue(&q);
      assert(q.kbase_seqnos.bo == &event_bo && releases == 0 && deletes == 0);
      return 0;
   }
   destroy_gpu_queue(&q.vk);
   if (scenario >= 2 && scenario <= 5) {
      assert(subject->kbase_seqnos.bo == &event_bo);
      assert(subject->kbase_import_queue == &import_queue);
      assert(logs && !releases && !freed && finished == 1 && lost == 1);
      assert(scenario == 2 ? deletes == 1 : deletes == 0);
      if (scenario == 3) assert(!unmaps && !terms);
      assert(scenario == 2 ? !ordinary_live : ordinary_live);
   } else {
      assert(!live_groups && releases == 1 && heaps == 1 && freed == 1 && finished == 1);
      assert(subject->kbase_seqnos.bo == NULL && subject->kbase_import_queue == NULL);
      assert(!ordinary_live && ordinary_cleanups == 1);
      assert(trace[count - 1] == 6);
      assert(scenario == 9 ? trace[count - 2] == 4 :
             (trace[count - 2] == 5 && trace[count - 3] == 4));
   }
   return 0;
}
""")
        result = subprocess.run(
            ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
             "-Wno-unused-function", "-I", str(mesa / "include"),
             str(source), "-o", str(cls.exe)],
            capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise AssertionError(result.stderr)

    def run_case(self, case):
        result = subprocess.run([str(self.exe), str(case)], timeout=5,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_group_tiler_delete_then_event_release(self):
        self.run_case(1)

    def test_delete_failure_retains_handle_bo_and_queue_metadata(self):
        self.run_case(2)

    def test_failed_completion_and_teardown_retain_all_gpu_resources(self):
        for case in (3, 4, 5):
            with self.subTest(case=case):
                self.run_case(case)

    def test_partial_initialization_uses_checked_teardown(self):
        for case in (6, 7, 8):
            with self.subTest(case=case):
                self.run_case(case)

    def test_no_import_handle_still_releases_event_bo_after_groups(self):
        self.run_case(9)

    def test_cleanup_queue_keeps_event_bo_alive(self):
        self.run_case(10)

    def test_failed_init_cleanup_preserves_causal_error_and_resources(self):
        for case in (11, 12, 13):
            with self.subTest(case=case):
                self.run_case(case)

    def test_termination_errno_survives_diagnostic_logging(self):
        for case in (14, 15):
            with self.subTest(case=case):
                self.run_case(case)


class PanVKSyncFileSnapshotTests(unittest.TestCase):
    def run_case(self, case):
        function = snapshot_function()
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "snapshot.c"
            exe = directory / "snapshot"
            source.write_text(r"""
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
typedef int VkResult;
#define VK_SUCCESS 0
#define VK_ERROR_OUT_OF_HOST_MEMORY (-1)
#define VK_ERROR_DEVICE_LOST (-4)
#define VK_ERROR_UNKNOWN (-13)
#define VK_ERROR_TOO_MANY_OBJECTS (-10)
#define VK_ERROR_INVALID_EXTERNAL_HANDLE (-1000072003)
#define container_of(ptr, type, member) \
   ((type *)((char *)(ptr) - offsetof(type, member)))
#define PANVK_KBASE_SYNC_TARGET_COUNT 3
typedef struct { bool locked; } mtx_t;
struct vk_device { int unused; };
struct vk_sync_type { void (*wait_many)(void); };
struct vk_sync { const struct vk_sync_type *type; };
enum kbase_cpu_sync_state {
   KBASE_CPU_SYNC_RESET, KBASE_CPU_SYNC_PENDING, KBASE_CPU_SYNC_WAITING,
   KBASE_CPU_SYNC_SIGNALED, KBASE_CPU_SYNC_FAILED
};
typedef VkResult (*panvk_kbase_sync_wait_func)(
   void *, const uint64_t *, uint64_t);
struct kbase_cpu_sync {
   struct vk_sync sync;
   mtx_t mutex;
   int cond;
   enum kbase_cpu_sync_state state;
   VkResult result;
   void *pending_data;
   panvk_kbase_sync_wait_func pending_wait;
   uint64_t targets[PANVK_KBASE_SYNC_TARGET_COUNT];
   uint64_t target_addrs[PANVK_KBASE_SYNC_TARGET_COUNT];
};
struct kbase_sync_file_waiter { int fd; };
static void kbase_cpu_sync_wait_many(void) { abort(); }
static const struct vk_sync_type kbase_cpu_sync_type = {
   .wait_many = kbase_cpu_sync_wait_many,
};
static unsigned locks, unlocks, duplicates, errors;
static int dup_error;
static bool real_fd;
static bool payload_locked;
static void mtx_lock(mtx_t *mutex)
{
   assert(!mutex->locked && !payload_locked);
   mutex->locked = payload_locked = true;
   locks++;
}
static void mtx_unlock(mtx_t *mutex)
{
   assert(mutex->locked && payload_locked);
   mutex->locked = payload_locked = false;
   unlocks++;
   errno = EINVAL;
}
static VkResult kbase_sync_file_wait_func(
   void *data, const uint64_t *targets, uint64_t timeout)
{ (void)data; (void)targets; (void)timeout; abort(); }
static VkResult other_wait(
   void *data, const uint64_t *targets, uint64_t timeout)
{ (void)data; (void)targets; (void)timeout; abort(); }
static VkResult vk_errorf(struct vk_device *device, VkResult result,
                          const char *format, ...)
{ (void)device; (void)format; errors++; return result; }
static int mock_fcntl(int fd, int command, ...)
{
   assert(payload_locked);
   assert(command == F_DUPFD_CLOEXEC);
   va_list args;
   va_start(args, command);
   int minimum = va_arg(args, int);
   va_end(args);
   assert(minimum == 0);
   duplicates++;
   if (real_fd)
      return fcntl(fd, command, minimum);
   assert(fd == 9);
   if (dup_error) { errno = dup_error; return -1; }
   return 19;
}
#define fcntl mock_fcntl
""" + function + r"""
#undef fcntl
int main(int argc, char **argv)
{
   assert(argc == 2);
   int test = atoi(argv[1]), fd = -1;
   int pipe_fds[2] = {-1, -1};
   struct vk_device device = {0};
   struct kbase_sync_file_waiter waiter = { .fd = 9 };
   const struct vk_sync_type device_type = kbase_cpu_sync_type;
   struct kbase_cpu_sync sync = {
      .sync.type = &device_type,
      .state = KBASE_CPU_SYNC_PENDING,
      .result = VK_SUCCESS,
      .pending_data = &waiter,
      .pending_wait = kbase_sync_file_wait_func,
   };
   const struct vk_sync_type foreign_type = {0};
   switch (test) {
   case 0: sync.sync.type = &foreign_type; break;
   case 1: sync.pending_wait = other_wait; break;
   case 2: sync.state = KBASE_CPU_SYNC_SIGNALED; break;
   case 3: break;
   case 4: dup_error = EMFILE; break;
   case 5:
      sync.state = KBASE_CPU_SYNC_FAILED;
      sync.result = VK_ERROR_DEVICE_LOST;
      break;
   case 6: sync.state = KBASE_CPU_SYNC_RESET; break;
   case 7: sync.state = KBASE_CPU_SYNC_WAITING; break;
   case 8: sync.pending_data = NULL; break;
   case 9: waiter.fd = -1; break;
   case 10: dup_error = ENFILE; break;
   case 11: dup_error = EBADF; break;
   case 12: dup_error = ENOMEM; break;
   case 13: dup_error = EIO; break;
   case 14:
      assert(pipe(pipe_fds) == 0);
      waiter.fd = pipe_fds[0];
      real_fd = true;
      break;
   default: return 2;
   }
   int original_fd = waiter.fd;
   void *original_payload = sync.pending_data;
   enum kbase_cpu_sync_state original_state = sync.state;
   VkResult result = panvk_kbase_sync_dup_sync_file_fd(&device, &sync.sync, &fd);
   assert(!sync.mutex.locked && locks == unlocks);
   assert(locks == (test == 0 ? 0u : 1u));
   if (test == 14) {
      assert(result == VK_SUCCESS && fd >= 0 && fd != original_fd);
      assert(duplicates == 1 && (fcntl(fd, F_GETFD) & FD_CLOEXEC));
      assert(fcntl(original_fd, F_GETFD) >= 0);
      assert(close(original_fd) == 0);
      assert(write(pipe_fds[1], "x", 1) == 1);
      char byte = 0;
      assert(read(fd, &byte, 1) == 1 && byte == 'x');
      assert(close(fd) == 0 && close(pipe_fds[1]) == 0);
   } else if (test == 3) {
      assert(result == VK_SUCCESS && fd == 19 && duplicates == 1);
   } else if (dup_error) {
      VkResult expected = dup_error == EMFILE || dup_error == ENFILE ?
         VK_ERROR_TOO_MANY_OBJECTS : dup_error == EBADF ?
         VK_ERROR_INVALID_EXTERNAL_HANDLE : dup_error == ENOMEM ?
         VK_ERROR_OUT_OF_HOST_MEMORY : VK_ERROR_UNKNOWN;
      assert(result == expected && fd == -1 && duplicates == 1 && errors > 0);
   } else if (test == 5) {
      assert(result == VK_ERROR_DEVICE_LOST && fd == -1 && duplicates == 0);
   } else if (test == 8 || test == 9) {
      assert(result == (test == 8 ? VK_ERROR_UNKNOWN :
                        VK_ERROR_INVALID_EXTERNAL_HANDLE));
      assert(fd == -1 && duplicates == 0 && errors > 0);
   } else {
      assert(result == VK_SUCCESS && fd == -1 && duplicates == 0);
   }
   assert(waiter.fd == original_fd && sync.state == original_state);
   assert(sync.pending_data == original_payload &&
          sync.pending_wait == (test == 1 ? other_wait : kbase_sync_file_wait_func));
   return 0;
}
""")
            result = subprocess.run(
                ["cc", "-std=c11", "-D_GNU_SOURCE", "-Wall", "-Wextra", "-Werror",
                 str(source), "-o", str(exe)], capture_output=True, text=True,
                timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(exe), str(case)], capture_output=True,
                                    text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_foreign_sync_payload_is_ineligible(self):
        self.run_case(0)

    def test_non_sync_file_pending_payload_is_ineligible(self):
        self.run_case(1)

    def test_signaled_payload_needs_no_duplicate(self):
        self.run_case(2)

    def test_pending_sync_file_is_duplicated_cloexec_under_mutex(self):
        self.run_case(3)

    def test_fcntl_failure_is_reported_without_consuming_payload(self):
        self.run_case(4)

    def test_failed_payload_preserves_device_lost(self):
        self.run_case(5)

    def test_reset_and_waiting_payloads_remain_on_cpu_path(self):
        for case in (6, 7):
            with self.subTest(case=case):
                self.run_case(case)

    def test_malformed_sync_file_payload_is_reported(self):
        for case in (8, 9):
            with self.subTest(case=case):
                self.run_case(case)

    def test_duplication_errno_is_preserved_and_classified(self):
        for case in (10, 11, 12, 13):
            with self.subTest(case=case):
                self.run_case(case)

    def test_real_duplicate_is_cloexec_and_survives_original_close(self):
        self.run_case(14)


@unittest.skipUnless(os.environ.get("PANVK_KBASE_TEST_MESA"),
                     "PANVK_KBASE_TEST_MESA must select a prepared read-only Mesa tree")
class PanVKFenceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        mesa = Path(os.environ["PANVK_KBASE_TEST_MESA"]).resolve()
        revision = subprocess.run(
            ["git", "-C", str(mesa), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5)
        if revision.returncode:
            raise AssertionError(revision.stderr)
        expected = json.loads((ROOT / "sources.lock").read_text())["mesaCommit"]
        if revision.stdout.strip() != expected:
            raise AssertionError("PanVK fixture source does not use sources.lock Mesa revision")

        text = (mesa / GPU_QUEUE).read_text()
        functions = []
        for name in (
                "kbase_fence_import_check_error",
                "kbase_subqueue_emit_job",
                "kbase_subqueue_publish",
                "kbase_subqueue_wait_seqno",
                "kbase_wait_sync_targets",
                "kbase_stage_gpu_wait",
                "panvk_queue_submit_ioctl_kbase",
                "panvk_queue_submit_process_signals_kbase",
                "kbase_finish_failed_teardown",
                "kbase_finish_fence_import_and_seqnos",
                "cleanup_queue",
                "panvk_per_arch(destroy_gpu_queue)"):
            functions.append(prepared_function(text, name))
        physical = (mesa / "src/panfrost/vulkan/panvk_physical_device.c").read_text()
        functions.append(prepared_function(physical, "kbase_cpu_sync_export_sync_file"))

        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        directory = Path(cls.temp.name)
        source = directory / "panvk.c"
        cls.exe = directory / "panvk"
        fixture = (ROOT / "tests/kbase_gpu_fence_wait_panvk.c").read_text()
        marker = "/* SOURCE_UNDER_TEST */"
        if fixture.count(marker) != 1:
            raise AssertionError("PanVK fixture must have exactly one source insertion point")
        source.write_text(fixture.replace(marker, "\n\n".join(functions)))
        cls.mesa = mesa
        cls.source = source
        cls.directory = directory
        result = subprocess.run(
            ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
             "-Wno-unused-function", "-Wno-unused-variable",
             "-Wno-unused-but-set-variable", str(source), "-o", str(cls.exe)],
            capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise AssertionError(result.stderr)

    def run_case(self, case):
        result = subprocess.run([str(self.exe), str(case)], timeout=5,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_successful_wait_control(self):
        self.run_case(0)

    def test_pending_fence_error_prevents_dependent_work(self):
        self.run_case(1)

    def test_completion_error_precedes_seqno_success(self):
        self.run_case(2)

    def test_already_signaled_fence_error_is_not_success(self):
        self.run_case(3)

    def test_value_visible_before_error_is_not_success(self):
        self.run_case(4)

    def test_stale_cached_payload_error_is_invalidated_before_call(self):
        self.run_case(5)

    def test_group_termination_precedes_import_delete_and_bo_release(self):
        self.run_case(6)

    def test_failed_import_delete_retains_handle_and_bo(self):
        self.run_case(7)

    def test_failed_group_termination_prevents_import_delete_and_bo_release(self):
        self.run_case(8)

    def test_prevalidation_reports_completed_import_error_immediately(self):
        self.run_case(9)

    def test_saturated_subqueue_rejects_staging_transactionally(self):
        self.run_case(10)

    def test_same_address_merges_max_seqno_at_capacity(self):
        self.run_case(11)

    def test_no_gpu_work_preserves_cpu_wait_path(self):
        self.run_case(12)

    def test_disabled_fence_wait_knob_preserves_cpu_wait_path(self):
        self.run_case(13)

    def test_enabled_fence_wait_knob_imports_pending_fence_without_cpu_wait(self):
        self.run_case(14)

    def test_import_seqno_exhaustion_uses_cpu_fallback(self):
        self.run_case(15)

    def test_partial_acceptance_at_last_target_is_fatal_and_never_reused(self):
        self.run_case(16)

    def test_emission_failure_after_import_keeps_event_bo_alive(self):
        self.run_case(17)

    def test_kick_failure_after_import_is_reported_without_freeing_event_bo(self):
        self.run_case(18)

    def test_output_sync_wait_reports_fence_error_without_new_submission(self):
        self.run_case(19)

    def test_foreign_completed_semaphore_does_not_bypass_import_error(self):
        self.run_case(20)

    def test_import_queue_is_created_with_distinct_reserved_cells(self):
        self.run_case(21)

    def test_create_failure_closes_snapshot_and_preserves_error(self):
        self.run_case(22)

    def test_first_enqueue_rejection_uses_diagnosed_cpu_fallback(self):
        self.run_case(23)

    def test_third_enqueue_failure_is_fatal(self):
        self.run_case(24)

    def test_saturated_fence_staging_does_not_import(self):
        self.run_case(25)

    def test_cpu_payload_is_invalidated_before_completion(self):
        self.run_case(26)

    def test_zero_target_callback_still_reports_import_error(self):
        self.run_case(27)

    def test_later_wait_failure_does_not_commit_partial_staging(self):
        self.run_case(28)

    def test_later_wait_failure_after_import_is_fatal(self):
        self.run_case(29)

    def test_later_wait_free_entry_keeps_import_error_guard(self):
        self.run_case(30)

    def test_active_queue_uses_doorbell_without_kick(self):
        self.run_case(31)

    def test_exported_output_waits_for_import_error_callback(self):
        self.run_case(32)

    def test_successful_import_export_uses_completed_cpu_callback(self):
        self.run_case(33)

    def test_export_with_zero_targets_cannot_bypass_import_error(self):
        self.run_case(34)

    def test_nonimport_export_keeps_async_cqs_path(self):
        self.run_case(35)

    def run_real_builder(self, diagnostics):
        generated = self.directory / "genxml"
        generated.mkdir(exist_ok=True)
        genxml = self.mesa / "src/panfrost/genxml"
        pack = subprocess.run(
            ["python3", str(genxml / "gen_pack.py"), str(genxml / "v11.xml")],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(pack.returncode, 0, pack.stderr)
        (generated / "v11_pack.h").write_text(pack.stdout)
        executable = self.directory / "real-builder"
        result = subprocess.run(
            ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
             "-Wno-unused-function", "-Wno-unused-variable",
             "-Wno-unused-but-set-variable", "-Wno-missing-field-initializers",
             "-Wno-unused-parameter", "-Wno-sign-compare",
             "-DPANVK_REAL_CS_BUILDER", "-D_GNU_SOURCE",
             f"-DPANVK_TEST_DIAGNOSTICS={int(diagnostics)}",
             "-DHAVE_ENDIAN_H", "-DHAVE_STRUCT_TIMESPEC",
             "-DHAVE_PTHREAD", "-DHAVE_THRD_CREATE", "-pthread",
             "-ffunction-sections", "-Wl,--gc-sections",
             "-I" + str(self.directory), "-I" + str(self.mesa / "include"),
             "-I" + str(self.mesa / "src"),
             "-I" + str(self.mesa / "src/panfrost"),
             str(self.source), str(self.mesa / "src/util/ralloc.c"),
             str(self.mesa / "src/util/u_dynarray.c"),
             "-o", str(executable)],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([str(executable), "0"], capture_output=True,
                                text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        print(f"Real v11 builder, diagnostics={diagnostics}: {result.stdout.strip()}")

    def test_real_builder_guarded_entries_fit_unchanged_ring_limit(self):
        self.run_real_builder(False)

    def test_real_builder_diagnostic_entries_fit_unchanged_ring_limit(self):
        self.run_real_builder(True)


class GPUFenceImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        directory = Path(cls.temp.name)
        (directory / "mali_kbase_ioctl.h").write_text(patched_uapi())
        cls.exe = directory / "bridge"
        source = directory / "bridge.c"
        source.write_text(r"""
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <errno.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <sys/ioctl.h>
#include "mali_kbase_ioctl.h"

struct pan_kmod_dev { int fd; bool csf; };
static bool kbase_kmod_is_csf(const struct pan_kmod_dev *dev) { return dev->csf; }
typedef struct { bool locked; } simple_mtx_t;
#define mtx_plain 0
static void simple_mtx_init(simple_mtx_t *m, int type)
{ (void)type; m->locked = false; }
static void simple_mtx_lock(simple_mtx_t *m)
{ assert(!m->locked); m->locked = true; }
static void simple_mtx_unlock(simple_mtx_t *m)
{ assert(m->locked); m->locked = false; }
static void simple_mtx_destroy(simple_mtx_t *m) { assert(!m->locked); }
#define p_atomic_read(p) __atomic_load_n((p), __ATOMIC_ACQUIRE)

struct sync_cell { uint64_t seqno; uint32_t error, padding; };
static struct sync_cell cells[4];
static unsigned creates, enqueues, deletes, closes, logs, releases;
static unsigned fail_enqueue, fail_delete, fail_create, fail_close, fail_alloc;
static bool partial_failure, fence_closed, fence_ready, fence_error;
struct pending_command {
   base_kcpu_queue_id id;
   uint8_t type;
   struct base_cqs_set_operation_info set;
};
static struct pending_command pending[256];
static unsigned pending_count;
static void mesa_loge(const char *format, ...)
{ (void)format; logs++; }
static void *mock_calloc(size_t count, size_t size)
{
   if (fail_alloc) { errno = ENOMEM; return NULL; }
   return calloc(count, size);
}
static int mock_close(int fd)
{
   assert(fd >= 0);
   closes++;
   fence_closed = true;
   if (fail_close) { errno = EIO; return -1; }
   return 0;
}
static void mock_free(void *ptr) { releases++; free(ptr); }
static int mock_ioctl(int fd, unsigned long request, void *arg)
{
   assert(fd >= 0);
   if (request == KBASE_IOCTL_KCPU_QUEUE_CREATE) {
      creates++;
      if (fail_create) { errno = ENOMEM; return -1; }
      struct kbase_ioctl_kcpu_queue_new *req = arg;
      for (unsigned i = 0; i < sizeof(req->padding); i++)
         assert(req->padding[i] == 0);
      req->id = creates;
      return 0;
   }
   if (request == KBASE_IOCTL_KCPU_QUEUE_DELETE) {
      deletes++;
      if (fail_delete) { errno = EBUSY; return -1; }
      /* The caller still owns both cells while DELETE can write them. */
      cells[0].seqno = cells[1].seqno = 7;
      cells[0].error = cells[1].error = 0;
      pending_count = 0;
      return 0;
   }
   assert(request == KBASE_IOCTL_KCPU_QUEUE_ENQUEUE);
   struct kbase_ioctl_kcpu_queue_enqueue *req = arg;
   assert(req->nr_commands == 1 && req->id > 0);
   for (unsigned i = 0; i < sizeof(req->padding); i++)
      assert(req->padding[i] == 0);
   struct base_kcpu_command *cmd = (void *)(uintptr_t)req->addr;
   enqueues++;
   for (unsigned i = 0; i < sizeof(cmd->padding); i++)
      assert(cmd->padding[i] == 0);
   if (fail_enqueue && enqueues == fail_enqueue) {
      partial_failure = true;
      errno = EACCES;
      return -1;
   }
   assert(pending_count < 256);
   struct pending_command *copy = &pending[pending_count++];
   copy->id = req->id;
   copy->type = cmd->type;
   if (cmd->type == BASE_KCPU_COMMAND_TYPE_FENCE_WAIT) {
      assert(!fence_closed);
      struct base_fence *fence = (void *)(uintptr_t)cmd->info.fence.fence;
      assert(fence->basep.fd >= 0 && fence->basep.stream_fd == -1);
   } else {
      assert(cmd->type == BASE_KCPU_COMMAND_TYPE_CQS_SET_OPERATION);
      assert(fence_closed);
      assert(cmd->info.cqs_set_operation.nr_objs == 1);
      assert(cmd->info.cqs_set_operation.padding == 0);
      copy->set = *(struct base_cqs_set_operation_info *)(uintptr_t)
         cmd->info.cqs_set_operation.objs;
      assert(copy->set.operation == BASEP_CQS_SET_OPERATION_SET);
      assert(copy->set.data_type == BASEP_CQS_DATA_TYPE_U64);
      for (unsigned i = 0; i < sizeof(copy->set.padding); i++)
         assert(copy->set.padding[i] == 0);
   }
   return 0;
}
/* Model FIFO completion only; it does not establish CPU/GPU ordering. */
static void process_pending(base_kcpu_queue_id id)
{
   assert(fence_ready && !partial_failure);
   unsigned kept = 0;
   for (unsigned i = 0; i < pending_count; i++) {
      struct pending_command *cmd = &pending[i];
      if (cmd->id != id) {
         pending[kept++] = *cmd;
         continue;
      }
      if (cmd->type == BASE_KCPU_COMMAND_TYPE_FENCE_WAIT)
         continue;
      assert(cmd->set.addr >= 0x1000 && cmd->set.addr <= 0x10c0);
      unsigned cell = (cmd->set.addr - 0x1000) / 64;
      cells[cell].seqno = cmd->set.val;
      cells[cell].error = fence_error;
   }
   pending_count = kept;
}
#define ioctl mock_ioctl
#define close mock_close
#define calloc mock_calloc
#define free mock_free
""" + added_code(HEADER, "enum kbase_kmod_csf_fence_import_result") + "\n" +
            added_code(SOURCE, "struct kbase_kmod_csf_fence_import_queue {") + r"""

static struct kbase_kmod_csf_fence_import_queue *create(struct pan_kmod_dev *dev)
{
   int error = -1;
   struct kbase_kmod_csf_fence_import_queue *queue =
      kbase_kmod_csf_fence_import_queue_create(
         dev, 0x1000, 0x1040, &cells[1].seqno, &error);
   assert(queue && error == 0);
   return queue;
}
static enum kbase_kmod_csf_fence_import_result
import(struct kbase_kmod_csf_fence_import_queue *queue, uint64_t target, int *error)
{
   fence_closed = false;
   return kbase_kmod_csf_fence_import(queue, 9, target, error);
}
int main(int argc, char **argv)
{
   assert(argc == 2);
   int test = atoi(argv[1]), error = -1;
   struct pan_kmod_dev dev = { .fd = 10, .csf = true };
   if (test == 0) {
      assert(sizeof(struct base_cqs_set_operation_info) == 24);
      assert(offsetof(struct base_cqs_set_operation_info, operation) == 16);
      assert(offsetof(struct base_cqs_set_operation_info, data_type) == 17);
      assert(sizeof(struct base_kcpu_command_cqs_set_operation_info) == 16);
      assert(sizeof(struct base_kcpu_command) == 24);
      assert(offsetof(struct base_kcpu_command, info) == 8);
      assert(_IOC_SIZE(KBASE_IOCTL_KCPU_QUEUE_ENQUEUE) == 16);
      return 0;
   }
   if (test == 9 || test == 10 || test == 16) {
      if (test == 9) fail_create = 1;
      if (test == 10) fail_alloc = 1;
      if (test == 16) dev.csf = false;
      assert(!kbase_kmod_csf_fence_import_queue_create(
         &dev, 0x1000, 0x1040, &cells[1].seqno, &error));
      assert(error == (test == 16 ? ENOTSUP : ENOMEM) && logs > 0);
      assert(creates == (test == 9 ? 1u : 0u));
      return 0;
   }
   if (test == 15) {
      const uint64_t pairs[][2] = {{0, 0x1040}, {0x1001, 0x1040},
         {0x1000, 0x1000}, {0x1000, 0x1010}, {0x1000, 0}};
      for (unsigned i = 0; i < sizeof(pairs) / sizeof(pairs[0]); i++) {
         assert(!kbase_kmod_csf_fence_import_queue_create(
            &dev, pairs[i][0], pairs[i][1], &cells[1].seqno, &error));
         assert(error == EINVAL && creates == 0);
      }
      return 0;
   }
   struct kbase_kmod_csf_fence_import_queue *queue = create(&dev);
   switch (test) {
   case 1:
   case 2:
   case 3:
      fail_enqueue = test;
      assert(import(queue, 7, &error) == (test == 1 ?
         KBASE_CSF_FENCE_IMPORT_REJECTED : KBASE_CSF_FENCE_IMPORT_FATAL));
      assert(error == EACCES && enqueues == (unsigned)test && closes == 1);
      if (test != 1) {
         assert(import(queue, 8, &error) == KBASE_CSF_FENCE_IMPORT_FATAL);
         assert(error == EACCES && enqueues == (unsigned)test && closes == 2);
      }
      fail_delete = 1;
      assert(kbase_kmod_csf_fence_import_queue_destroy(queue) == -1);
      assert(error == EACCES && releases == 0);
      fail_delete = 0;
      break;
   case 4: {
      struct kbase_kmod_csf_fence_import_queue *other =
         kbase_kmod_csf_fence_import_queue_create(
            &dev, 0x1080, 0x10c0, &cells[3].seqno, &error);
      assert(other && error == 0);
      assert(import(queue, 7, &error) == KBASE_CSF_FENCE_IMPORT_OK);
      assert(import(other, 7, &error) == KBASE_CSF_FENCE_IMPORT_OK);
      assert(creates == 2 && pending[0].id != pending[3].id);
      assert(pending[1].set.addr == 0x1000 && pending[2].set.addr == 0x1040);
      fence_ready = true;
      process_pending(pending[3].id);
      assert(pending_count == 3 && cells[1].seqno == 0);
      assert(cells[2].seqno == 7 && cells[3].seqno == 7);
      assert(kbase_kmod_csf_fence_import_queue_destroy(other) == 0);
      break;
   }
   case 5:
      assert(import(queue, 7, &error) == KBASE_CSF_FENCE_IMPORT_OK);
      assert(cells[1].seqno == 0 && pending_count == 3 && error == 0);
      fail_delete = 1;
      assert(kbase_kmod_csf_fence_import_queue_destroy(queue) == -1);
      assert(releases == 0 && cells[1].seqno == 0);
      fail_delete = 0;
      break;
   case 6:
      assert(import(queue, 7, &error) == KBASE_CSF_FENCE_IMPORT_OK);
      assert(cells[1].seqno == 0 && error == 0);
      fence_ready = fence_error = true;
      process_pending(pending[0].id);
      assert(cells[0].seqno == 7 && cells[1].seqno == 7);
      assert(cells[0].error == 1 && cells[1].error == 1);
      break;
   case 7:
      assert(import(queue, 0, &error) == KBASE_CSF_FENCE_IMPORT_REJECTED);
      assert(error == EINVAL && enqueues == 0 && closes == 1);
      assert(import(queue, (uint64_t)UINT32_MAX + 1, &error) ==
         KBASE_CSF_FENCE_IMPORT_REJECTED);
      assert(error == EINVAL && enqueues == 0 && closes == 2);
      assert(kbase_kmod_csf_fence_import(queue, -1, 1, &error) ==
         KBASE_CSF_FENCE_IMPORT_REJECTED);
      assert(error == EINVAL && enqueues == 0 && closes == 2);
      break;
   case 8:
      assert(import(queue, UINT32_MAX, &error) == KBASE_CSF_FENCE_IMPORT_OK);
      assert(pending[1].set.val == UINT32_MAX && pending[2].set.val == UINT32_MAX);
      assert(import(queue, (uint64_t)UINT32_MAX + 1, &error) ==
         KBASE_CSF_FENCE_IMPORT_REJECTED);
      assert(error == EINVAL && enqueues == 3);
      break;
   case 11:
   case 12:
      for (unsigned i = 1; i <= 85; i++)
         assert(import(queue, i, &error) == KBASE_CSF_FENCE_IMPORT_OK);
      assert(pending_count == 255);
      assert(import(queue, 86, &error) == KBASE_CSF_FENCE_IMPORT_REJECTED);
      assert(error == EAGAIN && enqueues == 255);
      if (test == 12) {
         /* The final SET may still occupy one slot after publishing done. */
         cells[1].seqno = 85;
         pending[0] = pending[254];
         pending_count = 1;
         for (unsigned i = 86; i <= 170; i++)
            assert(import(queue, i, &error) == KBASE_CSF_FENCE_IMPORT_OK);
         assert(pending_count == 256);
         assert(import(queue, 171, &error) == KBASE_CSF_FENCE_IMPORT_REJECTED);
         assert(error == EAGAIN && enqueues == 510);
      }
      break;
   case 13:
      fail_close = 1;
      assert(import(queue, 7, &error) == KBASE_CSF_FENCE_IMPORT_FATAL);
      assert(error == EIO && enqueues == 1 && closes == 1);
      break;
   case 14:
      fail_enqueue = fail_close = 1;
      assert(import(queue, 7, &error) == KBASE_CSF_FENCE_IMPORT_REJECTED);
      assert(error == EACCES && enqueues == 1 && closes == 1);
      break;
   case 17:
      assert(import(queue, 7, &error) == KBASE_CSF_FENCE_IMPORT_OK);
      assert(import(queue, 7, &error) == KBASE_CSF_FENCE_IMPORT_REJECTED);
      assert(error == EINVAL && enqueues == 3);
      assert(import(queue, 6, &error) == KBASE_CSF_FENCE_IMPORT_REJECTED);
      assert(error == EINVAL && enqueues == 3);
      break;
   default: return 2;
   }
   assert(kbase_kmod_csf_fence_import_queue_destroy(queue) == 0);
   assert(deletes > 0 && releases > 0);
   return 0;
}
""")
        result = subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                                 "-I", str(directory), str(source), "-o", str(cls.exe)],
                                capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stderr)

    def run_case(self, case):
        result = subprocess.run([str(self.exe), str(case)], timeout=5,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_uapi_struct_sizes_and_offsets(self):
        self.run_case(0)

    def test_first_enqueue_rejected_is_rejected(self):
        self.run_case(1)

    def test_partial_enqueue_is_fatal(self):
        self.run_case(2)

    def test_third_enqueue_failure_is_fatal(self):
        self.run_case(3)

    def test_independent_queues_make_progress(self):
        self.run_case(4)

    def test_pending_destroy_keeps_cqs_alive(self):
        self.run_case(5)

    def test_fence_error_is_not_success(self):
        self.run_case(6)

    def test_invalid_args_rejected_without_ioctl(self):
        self.run_case(7)

    def test_last_valid_target_and_out_of_range(self):
        self.run_case(8)

    def test_create_failure_is_reported(self):
        self.run_case(9)

    def test_allocation_failure_has_no_ioctl(self):
        self.run_case(10)

    def test_capacity_rejected_before_enqueue(self):
        self.run_case(11)

    def test_done_publication_before_retirement_preserves_capacity(self):
        self.run_case(12)

    def test_close_failure_after_acceptance_is_fatal(self):
        self.run_case(13)

    def test_close_failure_preserves_enqueue_error(self):
        self.run_case(14)

    def test_overlapping_or_unaligned_cells_are_rejected(self):
        self.run_case(15)

    def test_non_csf_device_has_no_ioctl(self):
        self.run_case(16)

    def test_accepted_target_is_never_reused(self):
        self.run_case(17)
