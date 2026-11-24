# Workflow — memory and synchronization audit

## When and prerequisites

Use for import/VA/cache/readback/fence/lifetime errors. Complete
[discovery](platform-discovery.md), then read
[GPU memory](../references/gpu-memory.md) and
[DMA-BUF/sync](../references/dma-buf-sync.md).
Identify backing/FD owner, UAPI/page, source/variant, exact binary and context.
Do not treat the known SAME_VA discrepancy as already repaired.

## Sources and steps

1. Trace alloc/import → returned flags/VA or cookie → CPU mmap → BO publication
   → use/cache/waits → close/munmap/MEM_FREE. Inspect success and each partial
   failure separately. NEED_MMAP-only must not be inferred to mean SAME_VA.
2. Compare the current path to the documented
   [README/import discrepancy](../references/gpu-memory.md#known-discrepancy--do-not-report-it-fixed).
   Record static disagreement without fabricating a Moto fault/leak.
3. Separate shared backing/placed-map support, cache visibility and execution
   fences. No MAP_FIXED outside a reserved range, arbitrary import-flag
   overrides or shadow fallback. Do not free/reuse possibly referenced VA.
4. Trace waiter/FD ownership through import, wait, timeout, reset, move and
   destroy. Inspect CLOEXEC, absolute-deadline/EINTR/revents and separate
   KCPU enqueue failures. Patch presence does not prove the variant is enabled.
5. Reuse matching historical cases first. For a future authorized correction,
   require focused host/mock cases for NEED_MMAP-only and mmap failures;
   timeout sub-ms/long/EINTR; POLLNVAL; FD duplication; first-enqueue-success/
   second-failure and cleanup. No fault injection into a device in use.
6. Only if the existing glibc sync-file fixture is approved and all prerequisites
   match, use its [documented procedure](../../../../tests/README.md:200):
   CSF 1.21, 4 KiB pages, approved executable/ICD in an isolated guest directory.

   ```sh
   rtk bypass sha256sum ./libvulkan_panfrost.so
   rtk bypass timeout -k 3s 20s ./sync-file-test ./libvulkan_panfrost.so
   ```

   This is a proposed target command, not a host invocation or transfer plan.
   PASS requires `SYNC-FILE-PASS 12 cycles`, exit 0, genuine pending FD
   before/after timeout, completion after signal and no FD growth.
   The fixture's deliberate initial `VK_TIMEOUT` and serial wait after its
   signal are expected test stages, not failed attempts or a hang. This
   exception never permits retries after a real failure or total-deadline expiry.
   Exit 77 is BLOCKED; other nonzero exits are FAIL. Different UAPI/page or
   absent fixture means stop, not layout adaptation by guess.

## Evidence, gates and stop

Deliver the ownership/VA/cache/fence trace, errno/state at first failure,
variant and binary identity, content versus FD-only checks and unresolved
kernel contracts. Android/glibc reports stay separate.
Static defects are FAIL static; readback/FD PASS does not establish other gates.

Stop on inconsistent flags/VA, wrong readback, cache/ioctl error, POLLNVAL,
FD growth, unexpected timeout, total-deadline expiry or device-lost. Preserve
logs; no retries after a real failure, reset or unsafe release/reuse. The
fixture's expected serial wait stages above are not failure retries.
Record unexecuted host/device/stability tests explicitly.

## Authorization boundary

No source fix, opt-in promotion, executable build, transfer, device test or
cleanup is authorized by this workflow. Use only the separately approved
isolated context and target-process stop mechanism.
