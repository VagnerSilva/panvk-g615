#!/usr/bin/env python3
"""Compile the experimental MEM_SYNC implementation with a recording ioctl."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class KbaseCoalesceMemSyncTests(unittest.TestCase):
    def test_coalescing_and_cleanup(self):
        mesa = Path(os.environ.get("MESA", ROOT / "work/mesa"))
        patch = (ROOT / "patches/experimental-kbase-sync/"
                 "003-kbase-coalesce-mem-sync.patch").read_text()
        postimage = "\n".join(
            line[1:] for line in patch.splitlines()
            if line.startswith((" ", "+")) and not line.startswith("+++")
        )
        start = postimage.index("static int\nkbase_deferred_bo_sync_cmp")
        implementation = postimage[start:]
        prepared = (mesa / "src/panfrost/lib/kmod/kbase_kmod.c").read_text()
        self.assertIn(implementation, prepared)
        harness = r"""
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

static unsigned allocated, released, logged, calls, fail_call;
static bool fail_alloc;
static void *test_malloc(size_t size) {
   if (fail_alloc) return NULL;
   allocated++;
   return malloc(size);
}
static void test_free(void *ptr) { released++; free(ptr); }
#define malloc test_malloc
#define free test_free
#include "util/stack_array.h"
#define mesa_loge(...) ((void)logged++)
#define container_of(ptr, type, member) \
   ((type *)((char *)(ptr) - offsetof(type, member)))
enum {
   PAN_KMOD_BO_SYNC_CPU_CACHE_FLUSH,
   PAN_KMOD_BO_SYNC_CPU_CACHE_FLUSH_AND_INVALIDATE,
   BASE_SYNCSET_OP_MSYNC,
   BASE_SYNCSET_OP_CSYNC,
   KBASE_IOCTL_MEM_SYNC
};
struct pan_kmod_bo { unsigned id; };
struct kbase_kmod_bo {
   struct pan_kmod_bo base;
   bool cpu_gpu_coherent;
   uint64_t gpu_va;
   void *cpu_ptr;
};
struct pan_kmod_deferred_bo_sync {
   struct pan_kmod_bo *bo;
   uint64_t start, size;
   unsigned type;
};
struct array { void *data; unsigned count; };
struct pan_kmod_dev { int fd; struct { struct array array; } pending_bo_syncs; };
#define util_dynarray_num_elements(a, type) ((a)->count)
#define util_dynarray_element(a, type, idx) (&((type *)(a)->data)[idx])
struct kbase_ioctl_mem_sync { uint64_t handle, user_addr, size; unsigned type; };
static struct kbase_ioctl_mem_sync emitted[4096];
static int pan_kmod_ioctl(int fd, int request, void *arg) {
   (void)fd;
   assert(request == KBASE_IOCTL_MEM_SYNC);
   emitted[calls++] = *(struct kbase_ioctl_mem_sync *)arg;
   if (fail_call && calls == fail_call) { errno = EIO; return -1; }
   return 0;
}
"""
        cases = r"""
static struct kbase_kmod_bo bos[2] = {
   {.gpu_va = 0x1000, .cpu_ptr = (void *)0x10000},
   {.gpu_va = 0x2000, .cpu_ptr = (void *)0x20000}
};
static int run(struct pan_kmod_deferred_bo_sync *ops, unsigned count) {
   struct pan_kmod_dev dev = {.pending_bo_syncs.array = {ops, count}};
   calls = logged = allocated = released = 0;
   return kbase_kmod_flush_bo_map_syncs(&dev);
}
#define OP(bo_index, offset, length, kind) \
   (struct pan_kmod_deferred_bo_sync){&bos[bo_index].base, offset, length, kind}
int main(void) {
   struct pan_kmod_deferred_bo_sync ops[4096], original[4096];
   assert(run(ops, 0) == 0 && calls == 0);
   ops[0] = OP(0, 64, 128, PAN_KMOD_BO_SYNC_CPU_CACHE_FLUSH);
   assert(run(ops, 1) == 0 && calls == 1 && allocated == 0);
   assert(emitted[0].user_addr == 0x10040 && emitted[0].size == 128);
   assert(emitted[0].type == BASE_SYNCSET_OP_MSYNC);
   bos[0].cpu_gpu_coherent = true;
   assert(run(ops, 1) == 0 && calls == 0);
   bos[0].cpu_gpu_coherent = false;
   ops[0] = OP(0, 128, 128, PAN_KMOD_BO_SYNC_CPU_CACHE_FLUSH);
   ops[1] = OP(0, 0, 192, PAN_KMOD_BO_SYNC_CPU_CACHE_FLUSH);
   ops[2] = OP(0, 256, 64, PAN_KMOD_BO_SYNC_CPU_CACHE_FLUSH);
   memcpy(original, ops, 3 * sizeof(*ops));
   assert(run(ops, 3) == 0 && calls == 1 && emitted[0].size == 320);
   assert(memcmp(ops, original, 3 * sizeof(*ops)) == 0);
   ops[1] = OP(0, 256, 64, PAN_KMOD_BO_SYNC_CPU_CACHE_FLUSH_AND_INVALIDATE);
   assert(run(ops, 2) == 0 && calls == 2);
   assert(emitted[0].type == BASE_SYNCSET_OP_MSYNC);
   assert(emitted[1].type == BASE_SYNCSET_OP_CSYNC);
   ops[1] = OP(0, 320, 64, PAN_KMOD_BO_SYNC_CPU_CACHE_FLUSH);
   assert(run(ops, 2) == 0 && calls == 2);
   ops[1] = OP(1, 128, 128, PAN_KMOD_BO_SYNC_CPU_CACHE_FLUSH);
   assert(run(ops, 2) == 0 && calls == 2);
   assert(emitted[0].handle != emitted[1].handle);
   for (unsigned i = 0; i < 4096; i++)
      ops[i] = OP(0, (4095 - i) * 64, 64,
                  PAN_KMOD_BO_SYNC_CPU_CACHE_FLUSH_AND_INVALIDATE);
   assert(run(ops, 4096) == 0 && calls == 1);
   assert(emitted[0].size == 4096 * 64 && allocated == released);
   fail_alloc = true;
   assert(run(ops, 4096) == -1 && calls == 0 && logged == 1);
   fail_alloc = false;
   fail_call = 1;
   assert(run(ops, 4096) == -1 && calls == 1 && logged == 1);
   assert(allocated == released);
   for (unsigned i = 0; i < 10; i++)
      ops[i] = OP(0, i * 128, 64, PAN_KMOD_BO_SYNC_CPU_CACHE_FLUSH);
   assert(run(ops, 10) == -1 && calls == 1 && allocated == released);
   fail_call = 0;
   return 0;
}
"""
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "coalesce.c"
            binary = Path(tmp) / "coalesce"
            source.write_text(harness + implementation + cases)
            subprocess.run(
                [os.environ.get("CC", "cc"), "-std=c11", "-O2",
                 "-Wall", "-Wextra", "-Werror", "-I", str(mesa / "src"),
                 str(source), "-o", str(binary)], check=True,
            )
            subprocess.run([str(binary)], check=True)


if __name__ == "__main__":
    unittest.main()
