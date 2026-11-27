# Workflow — CSF submission/lifecycle audit

## When and prerequisites

Use for group/queue creation, bind/mmap, kick, notification or teardown
failures. Complete [discovery](platform-discovery.md) and, for ABI issues,
[UAPI audit](uapi-audit.md). Confirm actual CSF context; JM remains a boundary.
Read [CSF lifecycle](../references/csf-jm.md).

## Sources and steps

1. Trace handshake/tracking/GLB → group → ring REGISTER → BIND → USER_IO mmap.
   Record handle/cookie/ring identities without substituting one for another.
   Inspect partial-create cleanup and first errno.
2. Follow [queue patch 007](../../../../patches/csf/007-gpu-queue-kbase.patch:1013)
   and later selected changes; group-per-subqueue/CSI0 are source behavior,
   not MCU/core-count or GLB capacity guarantees.
3. Trace publication, input offsets, active/doorbell/KICK and actual completion.
   Preserve wrapper logs even where callers do not propagate errors.
   Successful submit/kick alone is not completion.
4. Reuse existing notification logs. Classify read size/type and first
   queue/group fatal/timeout/OOM/fault; a device-level error latch is not recovery.
   Do not attach another reader to the driver's FD.
5. Check [085/111 behavior](../references/csf-jm.md#failure-and-notification-boundaries):
   nr 44 has no payload; SetEvent success may coexist with logged notification
   failure. Keep event memory/barriers in the PanVK/sync dependent domain.
6. Trace unmap → QUEUE_TERM → BO release → GROUP_TERM and creation-failure
   cleanup. Heap TERM worker is separate. No raw TERM/reset, early destruction,
   manufactured handles or unbounded reinitialization.

## Evidence, gates and stop

Deliver lifecycle/order, source locators, version/layout/page assumptions,
first error and observed completion/cleanup separately from expected behavior.
Where matching kernel/firmware cancellation or suspension semantics are absent,
record UNKNOWN rather than certify safety.

Static lifecycle PASS is not runtime PASS. An access/ABI prerequisite gap is
BLOCKED; a recorded queue fault is FAIL for its exact binary/context.
Stop new work at first timeout/fatal/device-lost/short read or unsafe cleanup.
No fairness, latency, endurance or recovery claim without matching tests.

## Authorization boundary

Only review sources and existing logs by default. A future minimum create/
submit/complete/destroy experiment must have explicit approval, bounded
workload/total timeout, isolated target and safe target-process stopping.
Do not reuse a long stress campaign as the minimum gate.
