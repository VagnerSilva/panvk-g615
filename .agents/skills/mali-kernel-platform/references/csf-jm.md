# CSF execution and the JM boundary

For management changes use [recipe C](implementation.md#recipe-c--modify-csf-management-without-changing-its-abi)
and [development](../workflows/development.md): mapped producer/consumer
functions, shared page layout and partial-create cleanup are the starting sites.

## Scope and evidence

Only Moto/G615 CSF is the operational target. A JM probe or historical JM
memory test does not certify CSF. Verify actual context and UAPI separately.
See [consolidation](../../../../docs/engineering/mali-kernel-platform/TECHNICAL_CONSOLIDATION.md#kbase-uapi-and-csf).

## Lifecycle to trace

1. VERSION_CHECK_CSF, SET_FLAGS/tracking and GLB query.
2. Group creation, ring allocation, REGISTER, BIND and USER_IO mmap.
3. Publish CS_INSERT, doorbell/KICK, then notifications and actual completion.
4. Unmap USER_IO, QUEUE_TERMINATE by ring VA and GROUP_TERMINATE by handle;
   trace partial-create cleanup separately.

Sources: [backend](../../../../patches/kbase-common/files/src/panfrost/lib/kmod/kbase_kmod.c:691)
and [queue integration](../../../../patches/csf/007-gpu-queue-kbase.patch:1013).
The inspected integration uses a group per subqueue and CSI0, not a queue
count derived from MC2. GLB counts/features are observations to collect,
not constants to invent.

## Failure and notification boundaries

- [Notification handling](../../../../patches/kbase-common/files/src/panfrost/lib/kmod/kbase_kmod.c:604)
  latches group error at device level. No automatic recovery is established.
  Short read, first errno and stage must survive reporting.
- A logged KICK error may not propagate through publication's return;
  successful submit is not completion proof.
- [085](../../../../patches/csf-v11/085-keep-descriptor-ring-and-vkevent-syncs-in-csf-event-memory.patch:22)
  uses CS_EVENT_SIGNAL nr 44, `_IO`, no payload.
  [111](../../../../patches/csf-v11/111-never-return-device-lost-from-set-reset-event.patch:39)
  logs notification failure without returning device-lost from event
  operations. SetEvent VK_SUCCESS is not notification-delivery proof.
- Heap TERM is not QUEUE/GROUP_TERM. Do not free/reuse referenced memory or
  send raw terminate/reset requests as a diagnostic shortcut.

Do not attach a second reader to a driver-owned notification FD.
Actual Moto layouts, page size, GLB facts, suspension/termination safety and
recovery are not established by static inspection.
Use [CSF audit](../workflows/csf-audit.md); memory ordering and fences belong
to [DMA-BUF/sync](dma-buf-sync.md).
