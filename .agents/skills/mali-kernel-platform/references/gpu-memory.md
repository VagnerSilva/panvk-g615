# GPU memory, mappings and ownership

For code changes use [recipe A and its edit-site map](implementation.md#recipe-a--repair-a-dma-buf-import)
before diagnostic collection. The known VA discrepancy already identifies
the invariant and dependent cleanup; do not investigate it from scratch.

## Scope and source

Trace allocation/import → GPU VA and backing → CPU mapping → use/cache/wait
→ release/error cleanup. Source:
[backend overlay](../../../../patches/kbase-common/files/src/panfrost/lib/kmod/kbase_kmod.c:1452)
and [memory consolidation](../../../../docs/engineering/mali-kernel-platform/TECHNICAL_CONSOLIDATION.md#memory-and-synchronization).
An overlay is an input, not a tested applied image.

## Known discrepancy — do not report it fixed

The [README](../../../../patches/kbase-common/files/README:12) documents
NEED_MMAP-only retaining real GPU VA, with SAME_VA using the cookie/mmap
relationship. The inspected
[import](../../../../patches/kbase-common/files/src/panfrost/lib/kmod/kbase_kmod.c:1512)
combines both flags and line 1542 always substitutes the CPU mapping as GPU VA.
No correcting later import post-image was identified in the targeted review.

Static consistency is FAIL. Actual Moto outflags/impact are unknown.
NEED_MMAP-only also follows the wrong cleanup classification; do not claim
measured faults/leaks or that every import fails. A future authorized fix must
cover VA selection and success/error close/munmap/MEM_FREE ownership.
Never toggle import flags merely to make a diagnostic pass.

## Other contracts

- DMA-BUF memory import/export duplicates with CLOEXEC; record exporter,
  importer, size, original/copy FD ownership and failure cleanup.
- Placed map needs suitable shared DMA-BUF backing. Do not invent a safe shadow
  fallback or use MAP_FIXED over arbitrary addresses.
  See [placed backing 091](../../../../patches/csf-v11/091-allocate-placeable-host-memory-from-the-dma-heap.patch:38).
- MEM_ALIAS, TLS alias, SAME_VA, grow-on-fault and Vulkan sparse are distinct.
  Keep sparse gated; internal aliases do not establish Vulkan sparse support.
- [237 EXEC/JIT](../../../../patches/csf-v11/237-kbase-exec-jit-and-ion-compatibility.patch:64)
  reserves zones, not 128 GiB of physical memory; initialization warning or
  enumeration does not establish functional JIT allocation.
- CPU pages are not GPU MMU granules. Coherent BO flags do not eliminate
  fence completion, barriers or lifetime obligations.

Kernel alias/import lifetime, cache policy, page size, allocator availability
and placed maps on Moto/glibc remain unqualified where evidence is absent.
Use [memory/sync audit](../workflows/memory-sync-audit.md).
