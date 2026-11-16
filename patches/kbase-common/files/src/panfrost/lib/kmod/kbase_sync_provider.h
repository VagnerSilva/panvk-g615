/* SPDX-License-Identifier: MIT */

#ifndef KBASE_SYNC_PROVIDER_H
#define KBASE_SYNC_PROVIDER_H

#include <errno.h>
#include <stdlib.h>
#include <stdatomic.h>

#include "util/log.h"
#include "util/macros.h"
#include "util/u_sync_provider.h"

struct kbase_sync_provider {
   struct util_sync_provider base;
   atomic_uint refs;
};

/*
 * Kbase has no syncobj handle namespace. PanVK uses its kbase_cpu_sync_type,
 * queue completion targets and KCPU sync_file export instead. Do not route
 * those objects through DRM ioctls or claim that a CPU-only handle is a GPU
 * fence. Keep unsupported entry points callable so accidental syncobj paths
 * fail explicitly rather than dereferencing a NULL callback.
 */
static int
kbase_sync_unsupported(const char *operation)
{
   mesa_loge("kbase: syncobj %s is not supported; use the Kbase vk_sync path",
             operation);
   errno = EOPNOTSUPP;
   return -EOPNOTSUPP;
}

static int
kbase_sync_create(UNUSED struct util_sync_provider *p, UNUSED uint32_t flags,
                  UNUSED uint32_t *handle)
{
   return kbase_sync_unsupported("create");
}

static int
kbase_sync_destroy(UNUSED struct util_sync_provider *p, UNUSED uint32_t handle)
{
   return kbase_sync_unsupported("destroy");
}

static int
kbase_sync_handle_to_fd(UNUSED struct util_sync_provider *p,
                        UNUSED uint32_t handle, UNUSED int *out_fd)
{
   return kbase_sync_unsupported("handle_to_fd");
}

static int
kbase_sync_fd_to_handle(UNUSED struct util_sync_provider *p, UNUSED int fd,
                        UNUSED uint32_t *handle)
{
   return kbase_sync_unsupported("fd_to_handle");
}

static int
kbase_sync_import_sync_file(UNUSED struct util_sync_provider *p,
                            UNUSED uint32_t handle, UNUSED int fd)
{
   return kbase_sync_unsupported("import_sync_file");
}

static int
kbase_sync_export_sync_file(UNUSED struct util_sync_provider *p,
                            UNUSED uint32_t handle, UNUSED int *out_fd)
{
   return kbase_sync_unsupported("export_sync_file");
}

static int
kbase_sync_wait(UNUSED struct util_sync_provider *p, UNUSED uint32_t *handles,
                 UNUSED unsigned count, UNUSED int64_t timeout,
                 UNUSED unsigned flags, UNUSED uint32_t *first_signaled)
{
   return kbase_sync_unsupported("wait");
}

static int
kbase_sync_reset(UNUSED struct util_sync_provider *p,
                  UNUSED const uint32_t *handles, UNUSED uint32_t count)
{
   return kbase_sync_unsupported("reset");
}

static int
kbase_sync_signal(UNUSED struct util_sync_provider *p,
                   UNUSED const uint32_t *handles, UNUSED uint32_t count)
{
   return kbase_sync_unsupported("signal");
}

static int
kbase_sync_query(UNUSED struct util_sync_provider *p, UNUSED uint32_t *handles,
                  UNUSED uint64_t *points, UNUSED uint32_t count,
                  UNUSED uint32_t flags)
{
   return kbase_sync_unsupported("query");
}

static int
kbase_sync_transfer(UNUSED struct util_sync_provider *p,
                     UNUSED uint32_t dst, UNUSED uint64_t dst_point,
                     UNUSED uint32_t src, UNUSED uint64_t src_point,
                     UNUSED uint32_t flags)
{
   return kbase_sync_unsupported("transfer");
}

static void
kbase_sync_finalize(struct util_sync_provider *p)
{
   struct kbase_sync_provider *provider =
      container_of(p, struct kbase_sync_provider, base);
   if (atomic_fetch_sub_explicit(&provider->refs, 1, memory_order_acq_rel) == 1)
      free(provider);
}

static struct util_sync_provider *
kbase_sync_clone(struct util_sync_provider *p)
{
   struct kbase_sync_provider *provider =
      container_of(p, struct kbase_sync_provider, base);
   /* Only the immutable dispatch table is shared, never the device fd. */
   atomic_fetch_add_explicit(&provider->refs, 1, memory_order_relaxed);
   return p;
}

static struct util_sync_provider *
kbase_sync_provider_create(void)
{
   struct kbase_sync_provider *provider = calloc(1, sizeof(*provider));
   if (!provider) {
      mesa_loge("kbase: failed to allocate sync provider");
      errno = ENOMEM;
      return NULL;
   }

   atomic_init(&provider->refs, 1);
   provider->base = (struct util_sync_provider) {
      .create = kbase_sync_create,
      .destroy = kbase_sync_destroy,
      .handle_to_fd = kbase_sync_handle_to_fd,
      .fd_to_handle = kbase_sync_fd_to_handle,
      .import_sync_file = kbase_sync_import_sync_file,
      .export_sync_file = kbase_sync_export_sync_file,
      .wait = kbase_sync_wait,
      .reset = kbase_sync_reset,
      .signal = kbase_sync_signal,
      .query = kbase_sync_query,
      .transfer = kbase_sync_transfer,
      /* NULL timeline callbacks advertise no syncobj timeline support. */
      .finalize = kbase_sync_finalize,
      .clone = kbase_sync_clone,
   };
   return &provider->base;
}

#endif
