# Nyushu on Moto G86: memory pressure and IRQ triage

## Scope and evidence

On 2026-11-25, two short Android/Bionic runs were observed on a Moto G86
with Mali-G615 MC2 and Kbase CSF 1.21 while the user ran a resource-intensive
scene. The first used the user-selected older driver; the second followed an
app restart with the current `003fix` driver. The exact scene state and FPS
were not measured. Each run has nine samples over approximately 43 seconds.

The loaded libraries matched the sizes of the local older `26e3f69d...` and
current `69f9f7ba...` ICDs respectively, but their loaded bytes were not
hashed in these runs. Their identities are therefore inferred, not proven.
The current ICD's hash and patch-series identity were independently verified
in the [isolated 003/007 tests](../../patches/experimental-kbase-sync/README.md#scoped-android-device-validation-of-003-and-007-2026-11-25).
Raw captures remain local session artifacts, not versioned in this report.

| Metric and source | Older run | Current run |
|---|---:|---:|
| Duration | 43.4 s | 43.6 s |
| Mali IRQ 436, `/proc/interrupts` | 7,611/s | 6,785/s |
| All IRQs, `/proc/stat` | 25,677/s | 23,898/s |
| `MemAvailable`, `/proc/meminfo` | 1,002-1,270 MiB | 1,325-1,539 MiB |
| Approximate Nyushu RSS, `/proc/<pid>/stat` | 2,888-3,137 MiB | 2,557-2,618 MiB |
| Nyushu major page faults, total increase | 2,113 | 3,388 |

RSS was derived from the sampled resident-page count using the confirmed
4 KiB page size. It includes process mappings and shared pages, is not
driver or GPU allocation, and is not PSS. A major fault is not itself proof
of swapping. `MemAvailable` is system-wide and must not be added to RSS or
compared to Vulkan heap usage as if they were the same quantity.

Android's low-memory killer logged two background-process kills during each
observation, including PSI-critical events. This establishes memory pressure,
not which component caused it. No reboot occurred during the two windows; in
the current run, an additional observer recorded an unchanged boot ID and
monotonic uptime for about 80 seconds. No new reboot, watchdog or panic entry
was found in the accessible records for that window. The cause of the earlier
device reboot remains unknown.

At 04:00:43, after the older measurement, the Nyushu process had a native
SIGSEGV on a null pointer in its GPU thread. Its recorded backtrace was in the
emulator, including `QueryCacheBase::CounterReport`, with no PanVK frame. This
is an app crash, not evidence of a device reboot; it does not rule out an
indirect driver contribution.

## Interpretation and limitations

- IRQ 436 is labelled `13000000.mali`; the particular interrupt cause is
  unknown. `/proc/stat` counts all system interrupts, not only the GPU.
  A rate alone is neither interrupt CPU time nor proof of a fault.
- The IRQ ranges overlapped substantially and the runs differ in process
  lifetime, memory state and potentially scene progression. The current
  series also differs by more than just the 003 correction. Without loaded
  hashes, FPS/frame times, repeated runs and a controlled workload, this is
  not a valid A/B performance result.
- Scoped tests show 003 ordering and the normal 007 wait path working, not
  that Nyushu exercises either path or that they reduce memory or IRQs.
  Long-duration stability and the original reboot cause remain unverified.

## Priorities for the next investigation

1. **Attribute memory pressure before changing an allocator.** With approval,
   sample the same identified Nyushu PID and scene alongside system
   `MemAvailable`, `SwapFree`, available memory PSI and low-memory-killer
   events. Record process RSS, `RssAnon`, `RssFile`, `RssShmem`, `VmSwap`,
   major-fault deltas and, if accessible, PSS from `smaps_rollup` or Android
   `dumpsys meminfo`. Use a light-scene control and a bounded return to the
   same scene. A persistent increase across repeated identical transitions
   suggests retained memory; a stable plateau alone does not establish a leak.
   Missing or denied counters remain unknown.
2. **Separate driver accounting from app memory.** The candidate contains
   [`csf-v11/223`](../../patches/csf-v11/223-driver-memory-accounting-panvk-debug-mem.patch),
   which can report `devmem`, private BO categories, command buffers,
   descriptors, TLS and tiler-heap context counts with `PANVK_DEBUG=mem`.
   Check whether the app can set the option and collect its output safely
   before proposing an instrumented run; compare it with an uninstrumented
   run because logging has overhead. Driver counters do not cover every
   kernel tiler-heap allocation and cannot simply be summed with RSS or PSS.
   Investigate object reuse or lifetime only in a category that actually
   grows; if driver counters stay small while app PSS grows, investigate the
   emulator's resources instead. Do not tune heap limits speculatively.
3. **Attribute IRQs and normalize the workload.** Identify the meanings of
   the Mali IRQs from the matching kernel/platform evidence if available.
   Collect confirmed displayed frames or frame times, submissions where
   available, IRQ deltas and CPU interrupt time in the same windows; compare
   IRQs per frame or submission as well as per second. Repeat alternating runs
   under matched resolution, scene, warm-up, thermal and memory conditions,
   confirming the loaded ICD hashes. If FPS or relevant counters cannot be
   obtained, the performance comparison remains blocked.
4. **Investigate sync signalling only if measurements point there.**
   [`csf-v11/077`](../../patches/csf-v11/077-use-system-scope-for-subqueue-sync-signals-on-kbase.patch)
   uses SYSTEM-scope signalling for Kbase cross-subqueue synchronization.
   A historical MC6 worklog associates those signals with interrupts; that
   is a hypothesis, not proof for this MC2 device. If a valid trace correlates
   signal frequency with IRQ 436, examine redundant submissions/signals and
   safe batching while preserving ordering and wakeups. Do not remove 077 or
   weaken synchronization without focused correctness and device tests.

Further device capture, app restarts, instrumentation and changes require
their own approval. Stop a run on loss of responsiveness, GPU fault,
device-lost, critical thermal state or unexpected restart. Do not clear logs,
change clocks or governors, escalate privileges, or reset the GPU.

## Gates

| Gate | Status |
|---|---|
| 003 kernel-order test and 007 normal wait on device | PASS, scoped |
| Nyushu short-window completion | PASS, two single runs |
| Loaded ICD identity during comparison | BLOCKED, hash not verified |
| Driver memory attribution and IRQ cause | UNKNOWN |
| Comparative performance and long-duration stability | NOT EXECUTED |
| Cause of original reboot | UNKNOWN |
