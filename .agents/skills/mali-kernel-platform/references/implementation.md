# Development map and implementation recipes

## Use the known edit sites first

This is the operational bridge from the existing
[consolidation](../../../../docs/engineering/mali-kernel-platform/TECHNICAL_CONSOLIDATION.md)
to code changes. Do not repeat its investigations. Locations below identify
input sources/patches; reconstruct the selected applied snapshot in an approved
disposable workspace before changing Mesa. Never edit the protected originals.

`K` below means Mesa target `src/panfrost/lib/kmod/kbase_kmod.c`, initially
provided by the
[Kbase overlay](../../../../patches/kbase-common/files/src/panfrost/lib/kmod/kbase_kmod.c).
Patch-file line numbers are input locators, not final source line numbers.
Later selected patches must be accounted for; absence of an applied snapshot
is BLOCKED for a real source implementation, not permission to guess contexts.

| Domain | Known functions/structures and edit sites | Preserved contract / dependent components | Focused acceptance |
|---|---|---|---|
| UAPI/ABI | `kbase_csf_group_create_layouts`, `kbase_csf_tiler_heap_init_layouts`, `kbase_csf_group_create_ioctl`, `kbase_kmod_csf_group_create`; [110](../../../../patches/csf-v11/110-select-kbase-csf-uapi-layouts-and-16k-pages.patch:157); `include/drm-uapi/mali_kbase_ioctl.h`, `kbase_kmod.h` | Encoded direction/type/nr/size, reserved zeros, version guards, per-device accepted-layout cache; no struct edit solely to satisfy a vendor error | Exact sizes/offsets and candidate order; EINVAL/ENOTTY advance, ENOMEM/access errors stop; Bionic/glibc builds separate |
| CSF management | `kbase_kmod_csf_queue_bind/term/kick`, `kbase_log_csf_notification`, `kbase_kmod_csf_wait_event` in [K](../../../../patches/kbase-common/files/src/panfrost/lib/kmod/kbase_kmod.c:692); `kbase_subqueue_publish`, `panvk_queue_submit_ioctl_kbase` in [007](../../../../patches/csf/007-gpu-queue-kbase.patch:709), target `src/panfrost/vulkan/csf/panvk_vX_gpu_queue.c` | REGISTER/BIND/cookie/three CPU pages before publication; queue/group/BO teardown order; observed error behavior (see recipe C); notifications have one consumer; queue and heap TERM are distinct | Mock register/bind/mmap failure edges, including failing TERM and delivered errno; cleanup order; page offsets for 4/16 KiB; bounded submit/complete/destroy only if authorized |
| Memory/VA | `struct kbase_kmod_bo`, `kbase_kmod_import_dmabuf`, `kbase_kmod_bo_import/alloc/free/mmap/munmap`, `kbase_kmod_alias_create/destroy` in [K](../../../../patches/kbase-common/files/src/panfrost/lib/kmod/kbase_kmod.c:1453) | GPU VA versus cookie/CPU pointer, owned mappings/FDs and cleanup; BO publication only after successful initialization | NEED_MMAP-only versus SAME_VA, NO_MMAP branch, both mmap failures, close/free ownership, no VA substitution for NEED_MMAP-only |
| Fences/KCPU | `struct kbase_cpu_sync`, `struct kbase_sync_file_waiter`, `kbase_cpu_sync_wait_one/import_sync_file/export_sync_file`, `kbase_sync_file_wait_func/waiter_free`, `panvk_kbase_sync_set_pending` in [004](../../../../patches/kbase-common/004-physical-device-kbase.patch:336), target `src/panfrost/vulkan/panvk_physical_device.c`; `kbase_kmod_csf_export_cqs64_fence` in [075](../../../../patches/csf-v11/075-export-kbase-sync-file-fences-through-a-kcpu-queue.patch:34) | State/mutex ownership, timeout retains waiter, successful terminal paths release it, CLOEXEC copies, absolute deadline and valid poll completion; partial kernel enqueue is not atomic | Signal/reset/move/import/wait/finish ownership; EINTR/deadline/sub-ms/long timeout/POLLNVAL; FD flags; first enqueue success/second failure, without fabricated kernel cancellation |
| Cache/optimization | `kbase_kmod_flush_bo_map_syncs`, `kbase_kmod_bo_wait` in [K](../../../../patches/kbase-common/files/src/panfrost/lib/kmod/kbase_kmod.c:1841); [003](../../../../patches/experimental-kbase-sync/003-kbase-coalesce-mem-sync.patch:16) | BO/op/range/ordering, overflow-safe ranges, coherent-BO rule, error propagation; bo_wait is not a fence wait; opt-in policy preserved | Same BO/op adjacent/overlapping ranges only; mixed-op ordering and malloc/ioctl errors; baseline/candidate content and timings, not syscall count alone |
| Initialization/firmware | `kbase_kmod_dev_create/destroy`, `kbase_query_csif_info`, `kbase_log_csf_notification` in [K](../../../../patches/kbase-common/files/src/panfrost/lib/kmod/kbase_kmod.c:1128); EXEC/JIT in [237](../../../../patches/csf-v11/237-kbase-exec-jit-and-ion-compatibility.patch:64) | Initialization order, partial cleanup and observed error latch; UAPI version is not firmware identity; no recovery/reset contract invented | Mock initialization failures; explicit unknown firmware/recovery behavior; observation-only properties |
| Android platform | `extract_file`, `Java_org_panvk_loadertest_MainActivity_runPanvkTest` in [loader test](../../../../tests/android-loader-app/jni/panvk_loader_test.c:28); historical `panvk_android_ahb_image_init → vk_android_get_ahb_layout → u_gralloc_get_buffer_basic_info` associated with [E-017 historical AHB evidence](../../../../docs/engineering/mali-kernel-platform/EVIDENCE_REGISTER.md) | Loaded path/marker/FD/file ownership and existing private ICD; no arbitrary layout/modifier inference or external-buffer writes; use exact snapshot for historical AHB symbols | Copy/read/partial-write failures and preservation in an isolated test; app versus privileged control; external-AHB deferred, not “fixed” by changing policy |
| Platform observations / glibc | `read_first_line`, `try_open`, `main` in [probe.c](../../../../tests/kbase-probe/probe.c:15); `main` in [handshake.c](../../../../tests/kbase-probe/handshake.c:16); [glibc build](../../../../scripts/build-glibc.sh:86) | Missing/denied data explicit, bounded reads; no submission from an observation; guest libc/loader/JSON/context are separate facts | Success/missing/permission/invalid-value observations using mocks; per-libc compile and future runtime separately, no inherited MC6 PASS |
| Mesa/Kraid integration | `pan_kmod` BO/dev operations and kmod dispatch; compiler [Meson integration](../../../../work/mesa/src/panfrost/compiler/meson.build:37) | Preserve shared interfaces, allocator order, compiler selection and Kraid integration; do not alter compiler algorithms to compensate for a Kbase/platform bug | Compile affected caller/header and both ABI configurations; hand off compiler internals to Kraid, never silently replace it |
| Job Manager | No active JM development target in the selected series | Preserve shared changes already carried in 235–240; do not restore retired JM families or reuse JM structs | Out-of-scope runtime request is stopped/routed, not implemented from CSF assumptions |

## Recipe A — repair a DMA-BUF import

1. Start at `kbase_kmod_bo_import → kbase_kmod_import_dmabuf`, then trace
   `kbase_kmod_bo_free`, `err_unmap_gpu` and `err_close_dmabuf`.
2. In the exact post-series import, make `same_va` depend only on
   `BASE_MEM_SAME_VA`. Publish GPU VA as mapping address only for SAME_VA;
   otherwise preserve `req.out.gpu_va`. Keep the GPU mapping for lifetime
   independently of that VA choice and leave coherency/NO_MMAP semantics intact.
3. Review every cleanup edge after changing classification. Once a non-SAME_VA
   region is successfully imported, ensure its owned region and duplicate FD
   are released on subsequent mapping errors and normal destruction. Do not
   double-free a SAME_VA cookie or close the caller's original FD.
4. Add focused cases for SAME_VA, NEED_MMAP-only, neither flag and both flags;
   distinct CPU/GPU addresses; GPU-mmap failure, CPU-mmap failure, NO_MMAP;
   FD duplication and cleanup. Do not change import flags to make tests pass.
5. Emit a small Kbase-family patch and metadata. A demonstration on the overlay
   must explicitly name that base and not claim applicability to patched Mesa.
   Run source/ABI build gates only in an approved disposable tree; actual
   outflags/content/runtime remain unvalidated until separately tested.

## Recipe B — change a sync-file wait path

1. Edit the current `kbase_sync_file_wait_func` and its callers/state ownership,
   not an unrelated BO cache path. Compare default and selected 004 behavior.
2. Recompute remaining monotonic time before every retry; preserve infinite and
   expired deadlines. Use a bounded conversion that does not turn a long finite
   timeout into a negative infinite poll, nor lose a positive sub-ms budget.
   A zero poll result completes a chunk, not necessarily the whole timeout:
   return VK_TIMEOUT only once the finite deadline has actually expired;
   otherwise recompute and poll again, including after an INT_MAX-clamped chunk.
3. Reject invalid FD/POLLNVAL and propagate the first real poll error through
   repository-standard VkResult/logging. Do not map every positive poll return
   to success; document POLLIN/error/hangup policy for sync_file.
4. If touching import/re-export, use atomic CLOEXEC duplication and retain
   caller ownership. If touching waiter lifecycle, timeout retains the payload;
   terminal success/error and reset/move/destroy follow the verified mutex and
   external-synchronization contract. Do not broaden concurrent destruction.
5. Test expired/sub-ms/long/infinite deadlines, EINTR/EAGAIN, invalid FD,
   POLLIN/POLLERR/POLLHUP/POLLNVAL, malloc/dup failure and state transitions.
   Require an unsignaled INT_MAX+1 ms budget: first poll uses INT_MAX, returns
   zero before the deadline, then the second poll uses the remaining 1 ms.
   Also require an unsignaled positive sub-ms budget to wait until its deadline.
   Keep partial KCPU enqueue a separate change unless its contract is required;
   unknown cancellation cannot be repaired by pretending DELETE rolls it back.

## Recipe C — modify CSF management without changing its ABI

For a page-layout refactor, start at `kbase_kmod_csf_queue_bind`, USER_IO
length and input/output consumers in `kbase_subqueue_publish` and completion.
Use one shared definition for three CPU pages, input `+page`, output `+2*page`;
preserve the returned BIND cookie directly. Update all consumers together.
Do not introduce a 4 KiB constant, change group-per-subqueue/CSI0 or heap TERM.
Test 4/16 KiB arithmetic and REGISTER/BIND/mmap partial failures with mocks,
plus header/caller compilation. A 16 KiB arithmetic test is not device proof.

The bind input does not save/restore errno around failure cleanup: a failing
TERM can replace BIND EACCES or mmap ENOMEM with cleanup EIO. This is a
preexisting limitation, not a preserved first-errno guarantee. Record the
initial failing stage/error separately from the errno delivered to the caller.
A behavior-preserving refactor must match the observed baseline, including
that replacement. Fixing save/restore is a separate behavioral correction
with approved scope and tests for failing TERM, not silent refactor cleanup.

For a compatibility change, edit selector/packing helpers and declarations in
110's targets together. Keep 1.21's 32→112→40 and 16→24 behavior, reserved
zeros and fault-report guard. Test EINVAL/ENOTTY versus ENOMEM/access failures
and cached acceptance. A nominal version alone cannot justify a new layout.

## Recipe D — implement an observable platform capability

A safe representative feature is a CPU-page-size observation in
`tests/kbase-probe/probe.c:main`. Use `sysconf(_SC_PAGESIZE)`, validate positive
results and print an explicit failure/unknown record on error. Add no new GPU
submission/ioctl, root requirement, vendor field or fallback value that looks
successful. Preserve existing probe records and exit/error conventions.
Edit this probe directly: it is outside Mesa and requires no delivery patch.

Test success, unavailable and invalid values with an isolated sysconf stub;
compile for the intended libc. Do not run the probe's other device accesses
as a host unit test. This observation does not certify firmware, GPU granule
or glibc runtime. Changes to JSON/consumer contracts require approved contract
updates and dependent tests, not an invented schema.

For AHB functionality, the existing metadata-access limitation is binding:
without a supported accessible metadata path, do not invent linear layout,
modify policy or extend the cookie probe. Report a blocked feature, not a
success-shaped import fallback.

## Refactoring and optimization

Refactor only a bounded common computation/ownership helper; keep public
signatures, lock order, error classification and default/opt-in behavior.
Compare before/after request sequences, states and error outputs with the same
focused fixture. No feature exposure or backend change as “cleanup”.

For cache optimization, start at `kbase_kmod_flush_bo_map_syncs` and 003,
prove same-BO/same-operation/range equivalence and preserve ordering across
different cache operations. Record baseline/candidate, identical device,
binary/variant, workload, repetitions, correctness, CPU submission timing and
observable ioctl counts. Fewer calls or historical timing estimates alone
are not a performance improvement. Without authorized comparable runs,
deliver a proposal with performance NOT EXECUTED.

Use the [development workflow](../workflows/development.md) for direct edits
outside Mesa, Mesa patches and build/test ordering; consult the
[decision matrix](decisions.md) before changing policy.
