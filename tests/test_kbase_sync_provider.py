#!/usr/bin/env python3
"""Compile the Kbase provider against the Mesa headers selected by MESA."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "patches/kbase-common/files/src/panfrost/lib/kmod"


class KbaseSyncProviderTests(unittest.TestCase):
    def test_provider_contract(self):
        mesa = Path(os.environ.get("MESA", ROOT / "work/mesa"))
        if not (mesa / "src/util/u_sync_provider.h").is_file():
            self.skipTest("Set MESA to a Mesa 27 checkout with u_sync_provider.h")

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "util").mkdir()
            (tmp / "util/log.h").write_text(
                "#define mesa_loge(...) test_log(__VA_ARGS__)\n"
            )
            source = tmp / "provider.c"
            source.write_text(r"""
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>

static bool fail_alloc;
static unsigned allocations, frees, logged_errors;

static void test_log(const char *format, ...)
{
   (void)format;
   logged_errors++;
}

static void *test_calloc(size_t count, size_t size)
{
   if (fail_alloc)
      return NULL;
   void *p = calloc(count, size);
   if (p)
      allocations++;
   return p;
}

static void test_free(void *p)
{
   assert(p);
   frees++;
   free(p);
}

#define calloc test_calloc
#define free test_free
#include "kbase_sync_provider.h"
#undef calloc
#undef free

#define UNSUPPORTED(expr) do { \
   errno = 0; \
   unsigned before = logged_errors; \
   assert((expr) == -EOPNOTSUPP); \
   assert(errno == EOPNOTSUPP); \
   assert(logged_errors == before + 1); \
} while (0)

static void *clone_thread(void *data)
{
   struct util_sync_provider *p = data;
   for (unsigned i = 0; i < 10000; i++) {
      struct util_sync_provider *clone = p->clone(p);
      assert(clone);
      clone->finalize(clone);
   }
   return NULL;
}

int main(void)
{
   fail_alloc = true;
   errno = 0;
   assert(!kbase_sync_provider_create());
   assert(errno == ENOMEM && logged_errors == 1);
   assert(allocations == 0 && frees == 0);

   fail_alloc = false;
   struct util_sync_provider *p = kbase_sync_provider_create();
   assert(p && allocations == 1);
   assert(!p->timeline_signal && !p->timeline_wait);

   uint32_t handle = 123, first = 456;
   uint64_t point = 789;
   int out_fd = -123;
   int fds[2];
   assert(pipe(fds) == 0);
   UNSUPPORTED(p->create(p, 0, &handle));
   UNSUPPORTED(p->destroy(p, handle));
   UNSUPPORTED(p->handle_to_fd(p, handle, &out_fd));
   UNSUPPORTED(p->fd_to_handle(p, fds[0], &handle));
   UNSUPPORTED(p->import_sync_file(p, handle, fds[0]));
   UNSUPPORTED(p->export_sync_file(p, handle, &out_fd));
   UNSUPPORTED(p->wait(p, &handle, 1, INT64_MAX, 0, &first));
   UNSUPPORTED(p->reset(p, &handle, 1));
   UNSUPPORTED(p->signal(p, &handle, 1));
   UNSUPPORTED(p->query(p, &handle, &point, 1, 0));
   UNSUPPORTED(p->transfer(p, handle, 1, handle, 2, 0));
   assert(handle == 123 && first == 456 && point == 789 && out_fd == -123);
   assert(fcntl(fds[0], F_GETFD) != -1);
   close(fds[0]);
   close(fds[1]);

   /* Cloning needs no new allocation and survives destruction of the owner. */
   fail_alloc = true;
   struct util_sync_provider *clone = p->clone(p);
   assert(clone);
   p->finalize(p);
   assert(frees == 0);
   UNSUPPORTED(clone->create(clone, 0, &handle));

   pthread_t threads[4];
   for (unsigned i = 0; i < 4; i++)
      assert(pthread_create(&threads[i], NULL, clone_thread, clone) == 0);
   for (unsigned i = 0; i < 4; i++)
      assert(pthread_join(threads[i], NULL) == 0);
   assert(frees == 0);
   clone->finalize(clone);
   assert(allocations == 1 && frees == 1);
   return 0;
}
""")
            executable = tmp / "provider"
            subprocess.run(
                [os.environ.get("CC", "cc"), "-std=c11", "-Wall", "-Wextra",
                 "-Werror", "-pthread", "-DHAVE_FUNC_ATTRIBUTE_UNUSED",
                 "-DHAVE_LIBDRM=1", "-I", str(tmp), "-I", str(OVERLAY),
                 "-I", str(mesa / "src"), "-I", str(mesa / "include"),
                 str(source), "-o", str(executable)],
                check=True,
            )
            subprocess.run([str(executable)], check=True, timeout=30)


if __name__ == "__main__":
    unittest.main()
