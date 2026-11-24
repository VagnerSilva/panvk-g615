# DMA-BUF, cache, fences and KCPU

For corrections use [recipe B and the sync/cache edit-site map](implementation.md#recipe-b--change-a-sync-file-wait-path).
For batching/refactoring use its [equivalence and measurement procedure](implementation.md#refactoring-and-optimization),
not historical syscall counts as a performance claim.

## Scope and separation

DMA-BUF backing/ownership, cache visibility, queue ordering and sync_file
completion are separate. Sharing pages or a poll-readable FD does not prove
correct content. Do not transfer Panthor DRM syncobj behavior to Kbase.
See [memory/sync consolidation](../../../../docs/engineering/mali-kernel-platform/TECHNICAL_CONSOLIDATION.md#memory-and-synchronization).

[BO wait/cache](../../../../patches/kbase-common/files/src/panfrost/lib/kmod/kbase_kmod.c:1833)
does not implement a fence wait per BO. Per-BO coherent outflags may skip
MEM_SYNC; explicit synchronization and lifetime remain necessary.
DMA_BUF_IOCTL_SYNC is not a universal replacement for Kbase MEM_SYNC or fences.

## Inspected defects and limits

| Contract | What must remain explicit |
|---|---|
| Default waiter | Successful wait loses the waiter pointer without freeing it |
| Experimental 004 | Supplies lifetime frees only opt-in; concurrent teardown still requires external synchronization |
| Sync-file FD copies | `dup` does not preserve CLOEXEC; memory-FD copies using CLOEXEC are a different path |
| Poll timeout | Repeated EINTR/EAGAIN reuses interval; sub-ms truncation and long-duration int conversion do not enforce an absolute deadline |
| Poll completion | POLLNVAL is not rejected and POLLIN is not required in inspected logic |
| KCPU export | Separate wait/signal ENQUEUEs; first-success/second-failure does not establish rollback or cancellation |
| Experimental 002 | Stages userspace targets with CPU fallback; not a partial-KCPU-enqueue, poll or FD repair |
| Experimental 003 | Cache-range coalescing is not device visibility or ordering validation |

Sources:
[waiter/poll](../../../../patches/kbase-common/004-physical-device-kbase.patch:608),
[KCPU export 075](../../../../patches/csf-v11/075-export-kbase-sync-file-fences-through-a-kcpu-queue.patch:29),
[002](../../../../patches/experimental-kbase-sync/002-android-release-queue-mesa27.patch:179),
[003](../../../../patches/experimental-kbase-sync/003-kbase-coalesce-mem-sync.patch:16),
[004](../../../../patches/experimental-kbase-sync/004-kbase-sync-file-waiter-lifetime.patch:44).
Read [experimental limitations](../../../../patches/experimental-kbase-sync/README.md)
before proposing the opt-in variant. Never promote it automatically.

Moto Android sync_fd/wait-signal reports concern a historical candidate,
not these corner cases or current-series stress/interprocess certification.
Kernel cancel/copyout/seqno-memory lifetime after enqueue failure remains
UNKNOWN. Use host/mock regression cases for an authorized correction before
hardware fault injection; no raw KCPU failure injection on a device in use.
Use [memory/sync audit](../workflows/memory-sync-audit.md).
