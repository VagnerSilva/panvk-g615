/* Host-only stubs around functions extracted from a selected prepared Mesa tree.
 * Builder calls are interpreted symbolically, not encoded or run on a GPU.
 */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <inttypes.h>
#include <errno.h>

#undef assert
#define assert(condition) do { \
   if (!(condition)) { \
      fprintf(stderr, "fixture assertion: %s (line %d)\n", #condition, __LINE__); \
      exit(90); \
   } \
} while (0)
#define CHECK(condition, reason) do { \
   if (!(condition)) { \
      fprintf(stderr, "case %d: %s\n", test, reason); \
      return 1; \
   } \
} while (0)
#define PAN_ARCH 11
#ifdef PANVK_REAL_CS_BUILDER
#include "genxml/cs_builder.h"
#endif
#define HAVE_PAN_KMOD_KBASE 1
#define PANVK_SUBQUEUE_COUNT 3
#define PANVK_KBASE_SYNC_TARGET_COUNT 3
#define PANVK_SUBQUEUE_VERTEX_TILER 0
#define PANVK_SUBQUEUE_FRAGMENT 1
#define PANVK_SUBQUEUE_COMPUTE 2
#define PANVK_KBASE_MAX_GPU_WAITS 6
#ifndef PANVK_TEST_DIAGNOSTICS
#define PANVK_TEST_DIAGNOSTICS 0
#endif
#define PANVK_DEBUG(flag) PANVK_TEST_DIAGNOSTICS
#define panvk_per_arch(name) name
#ifndef PANVK_REAL_CS_BUILDER
#define MIN2(a, b) ((a) < (b) ? (a) : (b))
#define MAX2(a, b) ((a) > (b) ? (a) : (b))
#define ALIGN_POT(v, a) (((v) + (a) - 1) & ~((a) - 1))
#define BITFIELD_BIT(i) (1u << (i))
#define u_foreach_bit(i, mask) \
   for (unsigned i = 0; i < 32; i++) if ((mask) & BITFIELD_BIT(i))
#define container_of(ptr, type, member) \
   ((type *)((char *)(ptr) - offsetof(type, member)))
#endif
typedef int VkResult;
#define VK_SUCCESS 0
#define VK_TIMEOUT 2
#define VK_INCOMPLETE 5
#define VK_ERROR_DEVICE_LOST (-4)
#define VK_ERROR_UNKNOWN (-13)
#define VK_ERROR_OUT_OF_DEVICE_MEMORY (-2)
#define VK_ERROR_OUT_OF_HOST_MEMORY (-1)
#define VK_ERROR_TOO_MANY_OBJECTS (-10)
#define p_atomic_read(p) __atomic_load_n((p), __ATOMIC_ACQUIRE)
#define p_atomic_set(p, v) __atomic_store_n((p), (v), __ATOMIC_RELEASE)
#define KBASE_RINGBUF_SIZE (64 * 1024)
#define KBASE_RING_JOB_MAX_SIZE 512
#define KBASE_WAIT_TIMEOUT_NS 10000000000ull
#define KBASE_SEQNO_LS_COPY_OFFSET 16
#define KBASE_SEQNO_MARK_PRE_CALL_OFFSET 24
#define KBASE_SEQNO_MARK_POST_CALL_OFFSET 32
#define KBASE_SEQNO_MARK_POST_WAIT_OFFSET 40
#define KBASE_SEQNO_STREAM_PROGRESS_OFFSET 48
#define KBASE_SEQNO_MARK_PRE_CALL 0x100000000000ull
#define KBASE_SEQNO_MARK_POST_CALL 0x200000000000ull
#define KBASE_SEQNO_MARK_POST_WAIT 0x300000000000ull
#define CS_USER_IO_INPUT_CS_INSERT 0
#define CS_USER_IO_OUTPUT_CS_EXTRACT 0
#define CS_USER_IO_OUTPUT_CS_ACTIVE 8
#ifndef PANVK_REAL_CS_BUILDER
#define SB_ID(name) SB_##name
#define SB_LS 1
#define SB_IMM_FLUSH 2
#define SB_DEFERRED_SYNC 3
#define SB_ITER(i) (i)
#define SB_WAIT_ITER(i) BITFIELD_BIT(i)
#define MALI_CS_SET_STATE_TYPE_SB_SEL_ENDPOINT 0
#define MALI_CS_SET_STATE_TYPE_SB_MASK_WAIT 1
#define MALI_CS_SET_STATE_TYPE_SB_SEL_OTHER 2
#define MALI_CS_SET_STATE_TYPE_SB_SEL_DEFERRED 3
#define MALI_CS_SET_STATE_TYPE_SB_MASK_STREAM 4
#define MALI_CS_FLUSH_MODE_CLEAN_AND_INVALIDATE 1
#define MALI_CS_OTHER_FLUSH_MODE_INVALIDATE 1
#define MALI_CS_SYNC_SCOPE_SYSTEM 1
#define MALI_CS_CONDITION_GREATER 0
#define MALI_CS_CONDITION_EQUAL 1
#define CS_INDEX_REGISTER 0
#else
#define SB_ID(name) SB_##name
#define SB_LS 1
#define SB_IMM_FLUSH 2
#define SB_DEFERRED_SYNC 3
#define SB_ITER(i) (i)
#define SB_WAIT_ITER(i) BITFIELD_BIT(i)
#endif

struct panvk_cs_sync64 { uint64_t seqno; uint32_t error, padding; };
union event_cell { struct panvk_cs_sync64 value; uint8_t bytes[64]; };
struct pan_kmod_bo { int unused; };
struct pan_kmod_dev { struct { uint64_t gpu_id; } props; };
struct vk_device { void *physical; int alloc; };
struct vk_queue { struct { struct vk_device *device; } base; bool lost; };
struct panvk_device {
   struct vk_device vk;
   struct { struct pan_kmod_dev *dev; } kmod;
   struct { struct { uint32_t all_iters_mask, all_mask; } sb; } csf;
   struct { void *decode_ctx; } debug;
};
struct panvk_physical_device { struct { struct pan_kmod_dev *dev; } kmod; };
struct panvk_priv_mem { uint64_t dev_addr; };
struct panvk_cs_subqueue_context { struct { uint64_t tiler_heap; } render; };
struct panvk_kbase_gpu_wait { uint64_t addr, seqno; };
struct kbase_kmod_csf_fence_import_queue {
   uint64_t payload_addr, done_addr;
   const volatile uint64_t *completed_seqno;
};
struct panvk_subqueue {
   struct panvk_priv_mem context;
   struct {
      void *ringbuf_cpu, *user_io;
      uint64_t ringbuf_dev, insert, emitted_jobs, heap_desc;
      uint32_t last_job_offset, last_last_job_offset, last_job_size;
      uint32_t last_job_entry_size, last_stream_size, last_flush_id;
      uint64_t last_stream_addr;
   } kbase;
};
struct panvk_gpu_queue {
   struct vk_queue vk;
   struct panvk_subqueue subqueues[PANVK_SUBQUEUE_COUNT];
   struct { struct panvk_priv_mem context; } tiler_heap;
   struct { struct pan_kmod_bo *bo; void *cpu; uint64_t dev; } kbase_seqnos;
   struct { void *sync; } utrace;
   struct panvk_priv_mem syncobjs;
   uint32_t syncobj_handle, kbase_tiler_submit_count;
   uint64_t kbase_tiler_work_count;
   struct panvk_kbase_gpu_wait kbase_gpu_waits[3][6];
   uint32_t kbase_gpu_wait_count[3];
   struct { uint64_t vt_jobs, frag_jobs; } kbase_retired_heaps[3];
   struct kbase_kmod_csf_fence_import_queue *kbase_import_queue;
   uint64_t kbase_import_seqno;
};
typedef VkResult (*sync_wait_func)(void *, const uint64_t *, uint64_t);
struct vk_sync {
   bool sync_file;
   struct panvk_gpu_queue *owner;
   uint64_t targets[3], addrs[3];
   sync_wait_func wait;
   void *data;
};
enum { KBASE_CPU_SYNC_PENDING, KBASE_CPU_SYNC_WAITING, KBASE_CPU_SYNC_SIGNALED };
struct kbase_cpu_sync {
   struct vk_sync sync;
   int mutex, state;
   sync_wait_func pending_wait;
   void *pending_data;
   uint64_t targets[3], target_addrs[3];
};
struct kbase_sync_file_waiter { int fd; };
struct vk_sync_wait { struct vk_sync *sync; uint64_t wait_value; };
struct vk_sync_signal { struct vk_sync *sync; uint64_t signal_value; };
struct vk_queue_submit {
   uint32_t wait_count, signal_count;
   const struct vk_sync_wait *waits;
   const struct vk_sync_signal *signals;
};
struct drm_panthor_queue_submit {
   uint32_t queue_index, stream_size, latest_flush;
   uint64_t stream_addr;
};
struct panvk_queue_submit {
   struct panvk_device *dev;
   struct panvk_physical_device *phys_dev;
   struct panvk_gpu_queue *queue;
   struct drm_panthor_queue_submit *qsubmits;
   uint32_t qsubmit_count;
   bool force_sync;
   uint64_t tiler_work_estimate, kbase_target_seqnos[3];
};
struct drm_panthor_csif_info {
   uint32_t cs_reg_count, unpreserved_cs_reg_count;
};
#ifndef PANVK_REAL_CS_BUILDER
struct cs_index { unsigned type, size, reg; };
struct cs_buffer { uint64_t *cpu; uint64_t gpu; uint32_t capacity; };
struct cs_builder_conf { unsigned nr_registers, nr_kernel_registers, ls_sb_slot; };
struct cs_builder { struct cs_buffer buffer; unsigned words; };
#endif

static union event_cell cells[5];
static uint64_t ring[3][KBASE_RINGBUF_SIZE / 8];
static uint64_t user_io[3][3 * 4096 / 8];
static struct pan_kmod_bo event_bo;
static struct pan_kmod_dev kmod = { .props.gpu_id = 0xb8a31030 };
static struct panvk_physical_device physical = { .kmod.dev = &kmod };
static struct panvk_device device = {
   .vk.physical = &physical, .kmod.dev = &kmod,
   .csf.sb = { .all_iters_mask = 0xff, .all_mask = 0xff },
};
static struct panvk_gpu_queue queue, owner;
static struct kbase_kmod_csf_fence_import_queue import_queue = {
   .payload_addr = 0x10c0, .done_addr = 0x1100,
   .completed_seqno = &cells[4].value.seqno,
};
static unsigned calls, publications, cpu_waits, imports, deletes, logs;
static unsigned groups, releases, output_successes, accepted_commands;
static unsigned lifecycle[8], lifecycle_count;
static uint64_t import_target, now;
static uint64_t last_wait_addr, last_wait_ref;
static bool bo_alive = true, group_terminated, semaphore_enabled, fence_enabled;
static bool fail_group, fail_delete, fail_kick, stale_gpu_cache;
static uint32_t cached_error;
static unsigned fail_enqueue;
static unsigned creates, closed_fds;
static unsigned raw_exports, complete_waits;
static bool fail_exported_import;
static bool fail_create, stale_cpu_payload;
static VkResult cpu_result = VK_SUCCESS, reserve_result = VK_SUCCESS;
#define mesa_loge(...) ((void)logs++)
#define mesa_logd(...) ((void)0)
#define mesa_logi(...) ((void)0)
#define pandecode_user_msg(...) ((void)0)
static void pandecode_cs_binary(void *ctx, uint64_t addr, uint64_t size, uint64_t gpu_id)
{ (void)ctx; (void)addr; (void)size; (void)gpu_id; }

static struct panvk_device *to_panvk_device(struct vk_device *dev)
{ return container_of(dev, struct panvk_device, vk); }
static struct panvk_physical_device *to_panvk_physical_device(void *dev)
{ return dev; }
static const struct drm_panthor_csif_info *panvk_get_csif_props(void *dev)
{
   (void)dev;
   static const struct drm_panthor_csif_info info = {64, 4};
   return &info;
}
static uint64_t panvk_priv_mem_dev_addr(struct panvk_priv_mem mem)
{ return mem.dev_addr; }
static uint64_t kbase_subqueue_seqno_dev_addr(struct panvk_gpu_queue *q, unsigned i)
{ (void)q; return 0x1000 + i * 64; }
static struct panvk_cs_sync64 *kbase_subqueue_seqno_cell(
   struct panvk_gpu_queue *q, unsigned i)
{ (void)q; assert(i < 5); return &cells[i].value; }
static struct panvk_cs_sync64 *mapped_cell(uint64_t addr)
{
   assert(bo_alive && addr >= 0x1000 && addr <= 0x1100 && !(addr % 64));
   return &cells[(addr - 0x1000) / 64].value;
}
static size_t kbase_seqno_stride(void) { return 64; }
static size_t kbase_kmod_page_size(void) { return 4096; }
static uint64_t kbase_heap_desc_addr(void *q) { (void)q; return 0x9000; }
static unsigned kbase_resource_mask(unsigned i) { return BITFIELD_BIT(i); }
static void kbase_cache_clean_range(const void *p, size_t n)
{ (void)p; (void)n; }
static void kbase_cache_invalidate_range(const void *p, size_t n)
{
   (void)n;
   if (stale_cpu_payload && p == &cells[3].value)
      cells[3].value.error = 1;
}
static uint64_t kbase_ring_qword(void *q, uint64_t off)
{ (void)q; (void)off; return 0; }
static void kbase_log_queue_syncobjs(void *q) { (void)q; }
static void kbase_log_subqueue_state(void *q, unsigned i, const char *s)
{ (void)q; (void)i; (void)s; }
static int64_t os_time_get_nano(void) { return now += 1000000; }
static int kbase_kmod_csf_wait_cqs64(void *dev, uint64_t addr, uint64_t val, int64_t ns)
{ (void)dev; (void)addr; (void)val; (void)ns; return -1; }
static int kbase_kmod_csf_wait_event(void *dev, int64_t ns)
{ (void)dev; (void)ns; return 0; }
static int kbase_kmod_csf_queue_kick(void *dev, uint64_t addr)
{ (void)dev; (void)addr; publications++; return fail_kick ? -1 : 0; }
static void kbase_gpu_wmb(void) {}
static VkResult vk_queue_set_lost(struct vk_queue *q, const char *format, ...)
{ (void)format; q->lost = true; logs++; return VK_ERROR_DEVICE_LOST; }
static bool vk_queue_is_lost(struct vk_queue *q) { return q->lost; }
static VkResult panvk_errorf(void *dev, VkResult result, const char *format, ...)
{ (void)dev; (void)format; logs++; return result; }
static VkResult kbase_subqueue_reserve_ring(struct panvk_gpu_queue *q, unsigned i)
{ (void)q; (void)i; return reserve_result; }
static bool gpu_queue_uses_kbase(void *dev) { (void)dev; return true; }
static bool kbase_gpu_waits_disabled(void) { return !semaphore_enabled; }
static bool debug_get_option_kbase_gpu_fence_waits(void) { return fence_enabled; }
static VkResult vk_sync_wait(void *dev, struct vk_sync *s, uint64_t val,
                             unsigned flags, uint64_t timeout)
{
   (void)dev; (void)s; (void)val; (void)flags; (void)timeout;
   cpu_waits++;
   return cpu_result;
}
#define VK_SYNC_WAIT_COMPLETE 0
#define VK_SYNC_WAIT_PENDING 1
static VkResult kbase_sync_file_wait_func(void *data, const uint64_t *targets,
                                        uint64_t timeout)
{ (void)data; (void)targets; (void)timeout; return VK_SUCCESS; }
static VkResult kbase_cpu_sync_wait_one(
   struct vk_device *dev, struct kbase_cpu_sync *ks, unsigned flags,
   uint64_t timeout)
{
   (void)dev;
   if (flags == VK_SYNC_WAIT_PENDING)
      return VK_SUCCESS;
   complete_waits++;
   cells[3].value.error = fail_exported_import;
   cells[4].value.seqno = 7;
   cells[2].value.seqno = 1;
   return ks->sync.wait(ks->sync.data, ks->sync.targets, timeout);
}
static int mtx_lock(int *mutex) { (void)mutex; return 0; }
static int mtx_unlock(int *mutex) { (void)mutex; return 0; }
static int dup(int fd) { (void)fd; assert(false); return -1; }
#define vk_errorf panvk_errorf
static int kbase_kmod_csf_export_cqs64_fence(
   void *dev, const uint64_t *addrs, const uint64_t *vals, unsigned count)
{
   (void)dev; (void)addrs; (void)vals; (void)count;
   raw_exports++;
   return 29;
}
static bool panvk_kbase_sync_peek_addrs(struct vk_sync *sync, void **data,
                                      uint64_t *targets, uint64_t *addrs)
{
   if (sync->sync_file)
      return false;
   *data = sync->owner;
   memcpy(targets, sync->targets, sizeof(sync->targets));
   memcpy(addrs, sync->addrs, sizeof(sync->addrs));
   return true;
}
static VkResult panvk_kbase_sync_dup_sync_file_fd(
   struct vk_device *dev, struct vk_sync *sync, int *fd)
{ (void)dev; *fd = sync->sync_file ? 19 : -1; return VK_SUCCESS; }
enum kbase_kmod_csf_fence_import_result {
   KBASE_CSF_FENCE_IMPORT_OK, KBASE_CSF_FENCE_IMPORT_REJECTED,
   KBASE_CSF_FENCE_IMPORT_FATAL
};
static struct kbase_kmod_csf_fence_import_queue *
kbase_kmod_csf_fence_import_queue_create(
   void *dev, uint64_t payload, uint64_t done,
   const volatile uint64_t *completed, int *error)
{
   (void)dev;
   assert(payload == 0x10c0 && done == 0x1100 &&
          completed == &cells[4].value.seqno && !*completed);
   creates++;
   *error = fail_create ? ENOMEM : 0;
   return fail_create ? NULL : &import_queue;
}
static int close(int fd) { assert(fd == 19); closed_fds++; return 0; }
static enum kbase_kmod_csf_fence_import_result kbase_kmod_csf_fence_import(
   struct kbase_kmod_csf_fence_import_queue *q, int fd,
   uint64_t target, int *error)
{
   assert(q && fd == 19 && bo_alive);
   imports++;
   import_target = target;
   *error = 0;
   if (fail_enqueue) {
      accepted_commands = fail_enqueue - 1;
      *error = EACCES;
      return fail_enqueue == 1 ? KBASE_CSF_FENCE_IMPORT_REJECTED :
                                KBASE_CSF_FENCE_IMPORT_FATAL;
   }
   accepted_commands = 3;
   return KBASE_CSF_FENCE_IMPORT_OK;
}
static void reset_trace_bufs(void *q) { (void)q; }
static void pan_kmod_flush_bo_map_syncs(void *dev) { (void)dev; }
static uint64_t kbase_tiler_heap_renew_work(void) { return UINT64_MAX; }
static uint32_t kbase_tiler_heap_renew_interval(void) { return UINT32_MAX; }
static VkResult kbase_renew_tiler_heap(void *q) { (void)q; return VK_SUCCESS; }
static VkResult kbase_subqueue_wait_seqno(
   struct panvk_gpu_queue *, uint32_t, uint64_t, uint32_t, bool, uint64_t);
static VkResult kbase_wait_sync_targets(
   void *, const uint64_t[PANVK_KBASE_SYNC_TARGET_COUNT], uint64_t);
static void panvk_kbase_sync_set_pending(
   struct vk_sync *sync, void *data, sync_wait_func wait,
   const uint64_t *targets, const uint64_t *addrs)
{
   sync->data = data;
   sync->wait = wait;
   memcpy(sync->targets, targets, sizeof(sync->targets));
   if (addrs)
      memcpy(sync->addrs, addrs, sizeof(sync->addrs));
   else
      memset(sync->addrs, 0, sizeof(sync->addrs));
}
static VkResult kbase_queue_wait_current(void *q, uint64_t timeout)
{ (void)q; (void)timeout; return VK_SUCCESS; }
static void panvk_mem_report(void *dev, bool final) { (void)dev; (void)final; }
static void finish_subqueue(void *q, unsigned i) { (void)q; (void)i; }
static void vk_sync_destroy(void *dev, void *sync) { (void)dev; (void)sync; }
static void finish_render_desc_ringbuf(void *q) { (void)q; }
static void panvk_pool_free_mem(void *mem) { (void)mem; }
static void lifecycle_event(unsigned event)
{ assert(lifecycle_count < 8); lifecycle[lifecycle_count++] = event; }
static void pan_kmod_bo_put(struct pan_kmod_bo *bo)
{
   assert(bo == &event_bo);
   lifecycle_event(3);
   releases++;
   bo_alive = false;
}
static int kbase_destroy_group(void *q)
{
   (void)q;
   lifecycle_event(1);
   groups++;
   if (fail_group) { logs++; return -1; }
   group_terminated = true;
   return 0;
}
static int kbase_kmod_csf_fence_import_queue_destroy(
   struct kbase_kmod_csf_fence_import_queue *q)
{
   assert(q == &import_queue && bo_alive && group_terminated);
   lifecycle_event(2);
   deletes++;
   if (fail_delete) { logs++; errno = EBUSY; return -1; }
   cells[3].value.seqno = cells[4].value.seqno = 7;
   return 0;
}
static void cleanup_tiler(void *q) { (void)q; }
static void destroy_group(void *q) { (void)q; }
static void pan_kmod_sync_destroy(void *dev, uint32_t handle)
{ (void)dev; (void)handle; }
static void vk_queue_finish(void *q) { (void)q; }
static void vk_free(void *alloc, void *q) { (void)alloc; (void)q; }

#ifndef PANVK_REAL_CS_BUILDER
enum operation {
   MOVE, WAIT, FLUSH, SLOT, LOAD_ERROR, CALL, ADD, STORE, IF, ELSE,
   BLOCK_END, NOP
};
struct instruction {
   enum operation op;
   struct cs_index dst, addr;
   uint64_t value;
   unsigned condition;
};
static struct instruction instructions[256];
static unsigned instruction_count, pc;
static uint32_t registers[64], pending_load;
static struct cs_index pending_dst;
static bool load_pending, flush_pending;
static void emit(struct cs_builder *b, struct instruction instruction)
{
   assert(instruction_count < 256);
   instructions[instruction_count++] = instruction;
   if (instruction.op != BLOCK_END)
      b->words++;
}
static uint64_t reg_value(struct cs_index r)
{
   assert(r.reg + r.size <= 64);
   return r.size == 1 ? registers[r.reg] :
          registers[r.reg] | ((uint64_t)registers[r.reg + 1] << 32);
}
static void reg_write(struct cs_index r, uint64_t value)
{
   assert((r.reg >= 60 || r.reg == 0) && r.reg + r.size <= 64);
   registers[r.reg] = value;
   if (r.size == 2)
      registers[r.reg + 1] = value >> 32;
}
static void cs_builder_init(struct cs_builder *b, const struct cs_builder_conf *c,
                            struct cs_buffer buffer)
{ assert(c->nr_registers == 64); b->buffer = buffer; b->words = 0; }
static struct cs_index cs_subqueue_ctx_reg(void *b)
{ (void)b; return (struct cs_index){ .size = 2 }; }
#define cs_set_state_imm32(b, ...) emit(b, (struct instruction){ .op = NOP })
#define cs_req_res(b, ...) emit(b, (struct instruction){ .op = NOP })
#define cs_heap_set(b, ...) emit(b, (struct instruction){ .op = NOP })
#define cs_error_barrier(b) emit(b, (struct instruction){ .op = NOP })
#define cs_wait_slots(b, ...) emit(b, (struct instruction){ .op = NOP })
#define cs_defer(mask, slot) (slot)
static void cs_move64_to(struct cs_builder *b, struct cs_index r, uint64_t value)
{ emit(b, (struct instruction){ .op = MOVE, .dst = r, .value = value }); }
static void cs_move32_to(struct cs_builder *b, struct cs_index r, uint32_t value)
{ cs_move64_to(b, r, value); }
static void cs_sync64_wait(struct cs_builder *b, bool reject_error,
                           unsigned condition, struct cs_index value,
                           struct cs_index addr)
{
   assert(!reject_error && condition == MALI_CS_CONDITION_GREATER);
   emit(b, (struct instruction){ .op = WAIT, .dst = value, .addr = addr });
}
static void cs_flush_caches(struct cs_builder *b, unsigned l2, unsigned lsc,
                            unsigned other, struct cs_index value, unsigned slot)
{
   (void)value;
   assert(l2 == MALI_CS_FLUSH_MODE_CLEAN_AND_INVALIDATE &&
          lsc == MALI_CS_FLUSH_MODE_CLEAN_AND_INVALIDATE &&
          other == MALI_CS_OTHER_FLUSH_MODE_INVALIDATE && slot == SB_IMM_FLUSH);
   emit(b, (struct instruction){ .op = FLUSH });
}
static void cs_wait_slot(struct cs_builder *b, unsigned slot)
{ emit(b, (struct instruction){ .op = SLOT, .value = slot }); }
static void cs_load32_to(struct cs_builder *b, struct cs_index dst,
                         struct cs_index addr, unsigned offset)
{
   assert(offset == offsetof(struct panvk_cs_sync64, error));
   emit(b, (struct instruction){ .op = LOAD_ERROR, .dst = dst, .addr = addr });
}
static void cs_call(struct cs_builder *b, struct cs_index addr, struct cs_index size)
{ emit(b, (struct instruction){ .op = CALL, .dst = size, .addr = addr }); }
static void cs_sync64_add(struct cs_builder *b, bool error, unsigned scope,
                          struct cs_index value, struct cs_index addr, unsigned slot)
{
   (void)error; (void)scope; (void)slot;
   emit(b, (struct instruction){ .op = ADD, .dst = value, .addr = addr });
}
static void cs_store64(struct cs_builder *b, struct cs_index value,
                       struct cs_index addr, unsigned offset)
{
   emit(b, (struct instruction){ .op = STORE, .dst = value,
                                 .addr = addr, .value = offset });
}
#define cs_store32 cs_store64
#define cs_if(b, cond, ref) \
   for (bool once = (emit(b, (struct instruction){ \
           .op = IF, .dst = ref, .condition = cond }), true); once; \
        once = (emit(b, (struct instruction){ .op = BLOCK_END }), false))
#define cs_else(b) \
   for (bool once = (emit(b, (struct instruction){ .op = ELSE }), true); once; \
        once = (emit(b, (struct instruction){ .op = BLOCK_END }), false))
static void cs_end(void *b) { (void)b; }
static void cs_builder_fini(void *b) { (void)b; }
static bool cs_is_valid(struct cs_builder *b) { return b->words <= b->buffer.capacity; }
static uint32_t cs_root_chunk_size(struct cs_builder *b) { return b->words * 8; }
#else
static struct cs_index cs_subqueue_ctx_reg(void *b)
{ (void)b; return (struct cs_index){ .type = CS_INDEX_REGISTER, .size = 2 }; }
#endif

/* SOURCE_UNDER_TEST */

#ifndef PANVK_REAL_CS_BUILDER
static void run_gpu(void)
{
   bool active = true, branch = true;
   while (pc < instruction_count) {
      struct instruction *i = &instructions[pc];
      if (i->op == IF) {
         assert(!load_pending && i->condition == MALI_CS_CONDITION_EQUAL);
         active = branch = reg_value(i->dst) == 0;
      } else if (i->op == ELSE) {
         active = !branch;
      } else if (i->op == BLOCK_END) {
         active = true;
      } else if (active) {
         switch (i->op) {
         case MOVE: reg_write(i->dst, i->value); break;
         case WAIT:
            last_wait_addr = reg_value(i->addr);
            last_wait_ref = reg_value(i->dst);
            if (mapped_cell(last_wait_addr)->seqno <= last_wait_ref)
               return;
            break;
         case FLUSH: flush_pending = true; break;
         case SLOT:
            if (i->value == SB_IMM_FLUSH && flush_pending) {
               cached_error = cells[3].value.error;
               flush_pending = false;
            }
            if (i->value == SB_LS && load_pending) {
               reg_write(pending_dst, pending_load);
               load_pending = false;
            }
            break;
         case LOAD_ERROR:
            pending_dst = i->dst;
            pending_load = stale_gpu_cache ? cached_error :
                           mapped_cell(reg_value(i->addr))->error;
            load_pending = true;
            break;
         case CALL:
            assert(reg_value(i->addr) == 0x8000 && reg_value(i->dst) == 8);
            calls++;
            break;
         case ADD: mapped_cell(reg_value(i->addr))->seqno += reg_value(i->dst); break;
         case STORE: break;
         case NOP: break;
         default: assert(false);
         }
      }
      pc++;
   }
}
#endif
static void setup(void)
{
   queue.vk.base.device = &device.vk;
   queue.kbase_seqnos.bo = &event_bo;
   queue.kbase_seqnos.cpu = cells;
   queue.kbase_seqnos.dev = 0x1000;
   queue.kbase_import_queue = &import_queue;
   owner.vk.base.device = &device.vk;
   for (unsigned i = 0; i < 3; i++) {
      queue.subqueues[i].kbase.ringbuf_cpu = ring[i];
      queue.subqueues[i].kbase.ringbuf_dev = 0x20000 + i * KBASE_RINGBUF_SIZE;
      queue.subqueues[i].kbase.user_io = user_io[i];
   }
}
static VkResult emit_import_wait(void)
{
   struct panvk_kbase_gpu_wait wait = { .addr = 0x1100, .seqno = 7 };
   queue.kbase_import_seqno = 7;
   return kbase_subqueue_emit_job(&queue, 2, 0x8000, 8, 0, kmod.props.gpu_id,
                                  &wait, 1);
}
static VkResult submit_wait(struct vk_sync *sync, bool work)
{
   struct drm_panthor_queue_submit job = {
      .queue_index = 2, .stream_addr = 0x8000, .stream_size = work ? 8 : 0,
   };
   struct panvk_queue_submit submit = {
      .dev = &device, .phys_dev = &physical, .queue = &queue,
      .qsubmits = &job, .qsubmit_count = 1,
   };
   struct vk_sync_wait wait = { .sync = sync };
   struct vk_queue_submit vk_submit = {
      .wait_count = sync ? 1 : 0, .waits = &wait,
   };
   return panvk_queue_submit_ioctl_kbase(&submit, &vk_submit);
}
int main(int argc, char **argv)
{
   assert(argc == 2);
   int test = atoi(argv[1]);
   setup();
#ifndef PANVK_REAL_CS_BUILDER
   if (test >= 32 && test <= 35) {
      struct kbase_cpu_sync output = { .state = KBASE_CPU_SYNC_PENDING };
      struct vk_sync_signal signal = { .sync = &output.sync };
      struct vk_queue_submit vk_submit = { .signal_count = 1, .signals = &signal };
      struct panvk_queue_submit submit = {
         .queue = &queue, .kbase_target_seqnos = {0, 0, test != 34},
      };
      queue.kbase_import_seqno = test == 35 ? 0 : 7;
      fail_exported_import = test == 32 || test == 34;
      panvk_queue_submit_process_signals_kbase(&submit, &vk_submit);
      output.pending_wait = output.sync.wait;
      output.pending_data = output.sync.data;
      memcpy(output.targets, output.sync.targets, sizeof(output.targets));
      memcpy(output.target_addrs, output.sync.addrs, sizeof(output.target_addrs));
      int fd = -1;
      VkResult result = kbase_cpu_sync_export_sync_file(&device.vk,
                                                       &output.sync, &fd);
      if (fail_exported_import) {
         CHECK(result == VK_ERROR_DEVICE_LOST && queue.vk.lost && !raw_exports &&
               complete_waits == 1 && fd == -1,
               "export bypassed callback and signaled success for a failed import");
      } else {
         CHECK(result == VK_SUCCESS && fd == 29 && raw_exports == 1 &&
               complete_waits == (unsigned)(test != 35),
               "successful export changed ordinary async path or skipped guarded wait");
      }
      return 0;
   }
#endif
#ifdef PANVK_REAL_CS_BUILDER
   (void)test;
   struct panvk_kbase_gpu_wait waits[6];
   for (unsigned i = 0; i < 6; i++)
      waits[i] = (struct panvk_kbase_gpu_wait){
         .addr = 0xabcdef123400ull + i * 64, .seqno = UINT32_MAX - i,
      };
   queue.kbase_import_seqno = 7;
   queue.tiler_heap.context.dev_addr = 0xabcdef123400ull;
   for (unsigned i = 0; i < 3; i++) {
      queue.subqueues[i].context.dev_addr = 0xabcdef123400ull;
      CHECK(kbase_subqueue_emit_job(&queue, i, 0xabcdef123400ull, UINT32_MAX, 0,
                                    kmod.props.gpu_id, waits, 6) == VK_SUCCESS,
            "real builder rejected maximum wait-count guarded entry");
      CHECK(queue.subqueues[i].kbase.last_job_entry_size <= 512,
            "real encoded ring entry exceeds unchanged 512-byte limit");
      printf("subqueue %u: %u bytes\n", i,
             queue.subqueues[i].kbase.last_job_entry_size);
   }
   return 0;
#else
   if (test == 30) {
      queue.kbase_import_seqno = 7;
      CHECK(kbase_subqueue_emit_job(&queue, 2, 0x8000, 8, 0,
                                    kmod.props.gpu_id, NULL, 0) == VK_SUCCESS,
            "later entry without explicit waits failed emission");
      cells[3].value.error = 1;
      cells[4].value.seqno = 7;
      run_gpu();
      CHECK(!calls && kbase_subqueue_wait_seqno(
               &queue, 2, 1, 0, false, 100000000) == VK_ERROR_DEVICE_LOST,
            "later wait-free entry bypassed the outstanding import guard");
      return 0;
   }
   if (test == 31) {
      *(uint32_t *)((uint8_t *)user_io[2] + 2 * 4096 +
                     CS_USER_IO_OUTPUT_CS_ACTIVE) = 1;
      queue.subqueues[2].kbase.insert = 64;
      CHECK(kbase_subqueue_publish(&queue, 2) == VK_SUCCESS && !publications &&
            *(uint32_t *)user_io[2] == 1 &&
            user_io[2][4096 / 8] == 64,
            "active queue doorbell path changed or issued an unnecessary kick");
      return 0;
   }
   if (test <= 5) {
      CHECK(emit_import_wait() == VK_SUCCESS, "wait-bearing ring entry did not emit");
      if (test == 2 || test == 3) {
         cells[2].value.seqno = 1;
         cells[2].value.error = test == 2;
         cells[3].value.error = 1;
         cells[4].value.seqno = 7;
         VkResult result = kbase_subqueue_wait_seqno(&queue, 2, 1, 0, false, 100000000);
         CHECK(result == VK_ERROR_DEVICE_LOST && queue.vk.lost,
               "completion accepted seqno success before fence error");
         return 0;
      }
      if (test == 0) {
         cells[4].value.seqno = 7;
         run_gpu();
         CHECK(calls == 1 && cells[2].value.seqno == 1,
               "successful fence did not execute exactly one dependent CALL");
         CHECK(kbase_subqueue_wait_seqno(&queue, 2, 1, 0, false, 100000000) == VK_SUCCESS,
               "successful completion control failed");
         return 0;
      }
      if (test != 5) {
         if (test == 4)
            cells[3].value.seqno = 7;
         run_gpu();
         CHECK(calls == 0 && pc < instruction_count,
               "dependent CALL ran before the done cell was published");
      } else {
         stale_gpu_cache = true;
      }
      cells[3].value.seqno = cells[4].value.seqno = 7;
      cells[3].value.error = 1;
      run_gpu();
      CHECK(calls == 0, "errored fence executed the dependent CALL");
      CHECK(kbase_subqueue_wait_seqno(&queue, 2, 1, 0, false, 100000000) ==
            VK_ERROR_DEVICE_LOST && queue.vk.lost,
            "fence error did not report device loss without another submission");
      return 0;
   }
   if (test >= 6 && test <= 8) {
      fail_delete = test == 7;
      fail_group = test == 8;
      destroy_gpu_queue(&queue.vk);
      if (test == 6) {
         CHECK(lifecycle_count == 3 && lifecycle[0] == 1 &&
               lifecycle[1] == 2 && lifecycle[2] == 3,
               "teardown is not group termination -> KCPU DELETE -> event BO release");
      } else {
         CHECK(bo_alive && queue.kbase_import_queue == &import_queue &&
               releases == 0 && logs > 0,
               "failed teardown released the event BO or silently discarded the handle");
         CHECK(test != 8 || deletes == 0, "DELETE ran after group termination failed");
      }
      return 0;
   }
   if (test == 9) {
      cells[3].value.error = 1;
      cells[4].value.seqno = queue.kbase_import_seqno = 7;
      CHECK(submit_wait(NULL, true) == VK_ERROR_DEVICE_LOST && queue.vk.lost &&
            publications == 0,
            "prevalidation did not report an already completed import error");
      return 0;
   }
   struct vk_sync sync = { .sync_file = true, .owner = &owner };
   if (test == 20) {
      semaphore_enabled = true;
      sync.sync_file = false;
      sync.targets[2] = cells[2].value.seqno = 1;
      sync.addrs[2] = 0x1080;
      owner.kbase_seqnos.cpu = cells;
      owner.kbase_import_seqno = cells[4].value.seqno = 7;
      cells[3].value.error = 1;
      CHECK(submit_wait(&sync, true) == VK_ERROR_DEVICE_LOST &&
            queue.vk.lost && !publications,
            "completed foreign semaphore bypassed its imported fence error");
      return 0;
   }
   if (test == 28 || test == 29) {
      semaphore_enabled = true;
      fence_enabled = test == 29;
      struct vk_sync first = { .sync_file = test == 29, .owner = &owner,
                              .targets = {7}, .addrs = {0x2000} };
      struct vk_sync second = { .sync_file = true };
      struct vk_sync_wait waits[] = {{.sync = &first}, {.sync = &second,
                                                       .wait_value = 1}};
      struct vk_queue_submit vk_submit = { .wait_count = 2, .waits = waits };
      struct drm_panthor_queue_submit job = {
         .queue_index = 2, .stream_addr = 0x8000, .stream_size = 8,
      };
      struct panvk_queue_submit submit = {
         .dev = &device, .phys_dev = &physical, .queue = &queue,
         .qsubmits = &job, .qsubmit_count = 1,
      };
      cpu_result = VK_TIMEOUT;
      VkResult result = panvk_queue_submit_ioctl_kbase(&submit, &vk_submit);
      CHECK(result == (test == 29 ? VK_ERROR_DEVICE_LOST : VK_TIMEOUT) &&
            cpu_waits == 1 && !publications &&
            !queue.kbase_gpu_wait_count[0] &&
            !queue.kbase_gpu_wait_count[1] &&
            !queue.kbase_gpu_wait_count[2],
            "later wait failure committed partial submission staging");
      CHECK(test != 29 || (queue.vk.lost && imports == 1 && bo_alive && !deletes),
            "failure after accepted import left a reusable queue");
      return 0;
   }
   if (test == 10 || test == 11) {
      semaphore_enabled = true;
      sync.sync_file = false;
      sync.targets[0] = 7;
      sync.addrs[0] = 0x2000;
      for (unsigned j = 0; j < 3; j++) {
         queue.kbase_gpu_wait_count[j] = j == 0 || test == 11 ? 6 : 0;
         for (unsigned k = 0; k < 6; k++)
            queue.kbase_gpu_waits[j][k] = (struct panvk_kbase_gpu_wait){
               .addr = (test == 11 ? 0x2000 : 0x3000) + 64 * k, .seqno = 3,
            };
      }
      struct panvk_kbase_gpu_wait before[3][6];
      uint32_t counts[3];
      memcpy(before, queue.kbase_gpu_waits, sizeof(before));
      memcpy(counts, queue.kbase_gpu_wait_count, sizeof(counts));
      cpu_result = VK_TIMEOUT;
      VkResult result = submit_wait(&sync, true);
      if (test == 10) {
         CHECK(result == VK_TIMEOUT && cpu_waits == 1 && imports == 0 &&
               publications == 0 &&
               !memcmp(before, queue.kbase_gpu_waits, sizeof(before)) &&
               !memcmp(counts, queue.kbase_gpu_wait_count, sizeof(counts)),
               "capacity fallback partially committed staged waits");
      } else {
         CHECK(result == VK_SUCCESS && cpu_waits == 0 &&
               queue.kbase_gpu_wait_count[0] == 6 &&
               queue.kbase_gpu_waits[0][0].addr == 0x2000 &&
               queue.kbase_gpu_waits[0][0].seqno == 7,
               "same-address wait did not merge MAX2(seqno) at capacity");
      }
      return 0;
   }
   if (test == 12 || test == 13) {
      fence_enabled = test == 12;
      CHECK(submit_wait(&sync, test != 12) == VK_SUCCESS &&
            cpu_waits == 1 && imports == 0 && queue.kbase_import_seqno == 0,
            "no-work/disabled-knob path did not preserve the CPU wait");
      return 0;
   }
   fence_enabled = true;
   if (test >= 21 && test <= 27) {
      if (test == 21 || test == 22) {
         queue.kbase_import_queue = NULL;
         fail_create = test == 22;
         VkResult result = submit_wait(&sync, true);
         CHECK(creates == 1 && cpu_waits == 0,
               "dedicated import queue was not created lazily");
         CHECK(test == 21 ? result == VK_SUCCESS && imports == 1 :
               result == VK_ERROR_OUT_OF_HOST_MEMORY && !imports &&
               closed_fds == 1 && bo_alive && !queue.kbase_import_queue,
               "CREATE failure lost the causal error or leaked the duplicate FD");
      } else if (test == 23 || test == 24) {
         fail_enqueue = test == 23 ? 1 : 3;
         VkResult result = submit_wait(&sync, true);
         CHECK(imports == 1 && accepted_commands == fail_enqueue - 1,
               "enqueue fault injection did not reach the import bridge");
         CHECK(test == 23 ? result == VK_SUCCESS && cpu_waits == 1 &&
               !queue.kbase_import_seqno && logs :
               result == VK_ERROR_DEVICE_LOST && queue.vk.lost && !cpu_waits &&
               queue.kbase_import_seqno == 1 && bo_alive && !deletes,
               "rejection and partial acceptance were not distinguished");
      } else if (test == 25) {
         queue.kbase_gpu_wait_count[0] = 6;
         for (unsigned i = 0; i < 6; i++)
            queue.kbase_gpu_waits[0][i] = (struct panvk_kbase_gpu_wait){
               .addr = 0x3000 + i * 64, .seqno = 3,
            };
         cpu_result = VK_TIMEOUT;
         CHECK(submit_wait(&sync, true) == VK_TIMEOUT && cpu_waits == 1 &&
               !imports && !publications && !queue.kbase_import_seqno &&
               queue.kbase_gpu_wait_count[0] == 6 &&
               !queue.kbase_gpu_wait_count[1] && !queue.kbase_gpu_wait_count[2],
               "saturated fence staging imported or partially published");
      } else {
         queue.kbase_import_seqno = cells[4].value.seqno = 7;
         cells[2].value.seqno = 1;
         cells[3].value.error = test == 27;
         stale_cpu_payload = test == 26;
         uint64_t targets[3] = {0, 0, test == 26};
         CHECK(kbase_wait_sync_targets(&queue, targets, 100000000) ==
               VK_ERROR_DEVICE_LOST && queue.vk.lost,
               "completion callback skipped CPU refresh or zero-target error");
      }
      return 0;
   }
   if (test == 14) {
      cpu_result = VK_TIMEOUT;
      CHECK(submit_wait(&sync, true) == VK_SUCCESS && imports == 1 &&
            cpu_waits == 0 && accepted_commands == 3,
            "enabled fence knob still waits for a pending fence on the CPU");
      return 0;
   }
   if (test == 15 || test == 16) {
      queue.kbase_import_seqno = UINT32_MAX - 1ull;
      fail_enqueue = test == 16 ? 2 : 0;
      VkResult result = submit_wait(&sync, true);
      if (test == 16) {
         CHECK(imports == 1 && accepted_commands == 1,
               "partial enqueue fault injection was never reached");
         CHECK(result == VK_ERROR_DEVICE_LOST && queue.vk.lost &&
               accepted_commands == 1 && cpu_waits == 0 &&
               queue.kbase_import_seqno == UINT32_MAX,
               "partial acceptance at the last target was not fatal and consumed");
         unsigned previous_imports = imports;
         CHECK(submit_wait(&sync, true) == VK_ERROR_DEVICE_LOST &&
               imports == previous_imports && queue.kbase_import_seqno == UINT32_MAX,
               "lost queue retried or reused the last import target");
      } else {
         CHECK(result == VK_SUCCESS && imports == 1 &&
               import_target == UINT32_MAX && queue.kbase_import_seqno == UINT32_MAX,
               "last UINT32_MAX import target was not reserved");
         run_gpu();
         CHECK(last_wait_addr == import_queue.done_addr &&
               last_wait_ref == UINT32_MAX - 1ull,
               "last target did not use the UINT32_MAX-1 wait reference");
         unsigned previous_imports = imports;
         unsigned previous_logs = logs;
         CHECK(submit_wait(&sync, true) == VK_SUCCESS &&
               imports == previous_imports && cpu_waits == 1 &&
               queue.kbase_import_seqno == UINT32_MAX && logs > previous_logs,
               "exhaustion reset the counter, imported, or used silent CPU fallback");
      }
      return 0;
   }
   if (test == 17 || test == 18) {
      reserve_result = test == 17 ? VK_ERROR_UNKNOWN : VK_SUCCESS;
      fail_kick = test == 18;
      VkResult result = submit_wait(&sync, true);
      CHECK(imports == 1 && accepted_commands == 3,
            "fence import was not accepted before the injected emission/kick failure");
      CHECK(result == VK_ERROR_DEVICE_LOST && queue.vk.lost && bo_alive && deletes == 0,
            "post-import emission/kick failure was ignored or released the event BO");
      return 0;
   }
   if (test == 19) {
      struct vk_sync output = {0};
      struct vk_sync_signal signal = { .sync = &output };
      struct vk_queue_submit vk_submit = { .signal_count = 1, .signals = &signal };
      struct panvk_queue_submit submit = {
         .queue = &queue, .kbase_target_seqnos = {0, 0, 1},
      };
      queue.kbase_import_seqno = cells[4].value.seqno = 7;
      cells[3].value.error = 1;
      cells[2].value.seqno = 1;
      panvk_queue_submit_process_signals_kbase(&submit, &vk_submit);
      assert(output.wait);
      VkResult result = output.wait(output.data, output.targets, 100000000);
      output_successes += result == VK_SUCCESS;
      CHECK(result == VK_ERROR_DEVICE_LOST && queue.vk.lost && output_successes == 0,
            "output sync callback reported success for an errored import");
      return 0;
   }
   return 2;
#endif
}
