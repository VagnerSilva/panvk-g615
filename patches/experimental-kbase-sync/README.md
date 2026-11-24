# Kbase Android release synchronization

## Inactive fence-import draft (006, transactional PanVK integration)

`006-kbase-kcpu-gpu-fence-wait.patch` prepares the SET UAPI and an isolated
Kmod queue for three FIFO commands: FENCE_WAIT, SET payload/error, SET done.
It also provides `panvk_kbase_sync_dup_sync_file_fd`, which identifies the
device-local Kbase sync type by its wait callback and duplicates an eligible
PENDING sync-file FD with `F_DUPFD_CLOEXEC` while holding the payload mutex.
The original FD, payload and state are unchanged. The caller owns a returned
duplicate; the import bridge consumes it even on rejection. Success with
FD `-1` means no duplicate was produced and preserves the existing CPU wait
path; it is not proof that the dependency completed. RESET and WAITING are
not eligible, FAILED propagates its stored error, and malformed payloads
or duplication errors return a diagnostic VkResult.
It is an unqualified draft, not part of the default or legacy series.
It now includes PanVK submission, guarded CALL and completion error checks.
`PANVK_KBASE_GPU_FENCE_WAITS` defaults to false. There is still no build flag
or provenance variant selecting 006.
Do not apply or promote it as a working GPU fence-wait implementation.

Host regression tests compile its actual added code with mocked KCPU
ioctls. They cover partial acceptance, owned-FD closure, causal errors,
retryable DELETE, independent queues, the UINT32_MAX domain and 85-triple
capacity including a final done SET not yet retired. Snapshot tests cover
copied device-local sync types, states, error classification and errno
preservation across unlock. A host pipe checks actual FD_CLOEXEC and
duplicate lifetime after the original FD closes; this is not a sync-file
or GPU execution test:

```sh
python3 -m unittest discover -s tests -p 'test_kbase_*wait*.py' -v
```

On 2026-11-24, the snapshot's 15 cases (10 test methods) went RED to GREEN;
the combined bridge/snapshot/WAIT_ANY suite passed 29 tests. The five-file
draft passed `git apply --check --whitespace=error -v` against an isolated
copy of its exact prepared input blobs without application or offsets.

Both cells must remain alive until DELETE succeeds. Before allowing DELETE
to drain dependencies, future PanVK integration must confirm termination of
all CSF consumers. A CPU error store before DELETE is not a substitute:
the drained SET can overwrite it. GPU cross-cell visibility/order,
error-before-completion handling, full-series replay, Android/glibc builds
and device execution remain separate, unexecuted acceptance gates.

The checked-teardown revision additionally changes the real Kmod queue/group
termination APIs to return status, preserving errno across diagnostics.
Queue TERM precedes USER_IO unmap; failure retains the mapping and ring BO.
PanVK checks all consumer groups before tiler cleanup, import-queue DELETE and
event-BO release. `cleanup_queue` no longer releases `kbase_seqnos.bo`.
Partial group initialization uses the same checked caller cleanup.
Ordinary GPU-visible queue allocations are also freed only after successful
CSF termination. On Kbase, `init_queue` delegates failure cleanup to its
caller, which tracks whether initialization started. Panthor keeps its
existing cleanup order.

CSF teardown failure retains all remaining GPU-visible queue allocations;
import DELETE failure retains the import queue and event BO. Both failures
retain the driver queue allocation. The Vulkan queue is marked lost and
finished/detached so device-init cleanup cannot destroy it a second time.
The original initialization error is still returned. Retention on this fatal
path intentionally sacrifices resource reclamation; it does not permit retry
through the finished Vulkan queue.

`CheckedFenceTeardownTests` extracts the actual Kmod and PanVK functions from
a selected prepared tree. It covers queue/group TERM, USER_IO unmap and DELETE
failures, partial initialization, errno preservation, no-import cleanup and
the event BO lifetime. The eight test methods and the three existing symbolic
teardown cases passed; bridge/snapshot/WAIT_ANY regressions bring the focused
suite to 40 passing tests. At that teardown-only revision, the full 20-case
Task 3 integration suite still had 12 RED cases for absent integration.
The lifetime regression exercised actual `init_queue` failures and failed
completion waits followed by TERM/unmap failures: nine scenarios failed
before deferring ordinary cleanup, and the focused suite then passed.
The revised seven-file draft passed strict application checks against its
post-default-series input. These host checks do not prove kernel/firmware
termination or CPU/GPU ordering; full Mesa builds and device tests of this
revision remain NOT EXECUTED. The 006 safety gate stays BLOCKED.

### Authorized inactive integration preparation

The user separately authorized submission call sites and host tests in this
inactive draft, without closing gate 1.3. The twelve original RED cases now
pass. Submission stages all waits locally before committing, lazily creates
the dedicated KCPU queue, distinguishes rejection from fatal partial
acceptance, and never resets or wraps the UINT32_MAX import counter.
Capacity/exhaustion/rejection use diagnosed CPU fallback without publishing
partial staging; failures after accepted imports lose the queue and retain
the event BO.

Each guarded entry waits on reserved done cell 4, invalidates GPU caches,
then loads the error from payload cell 3 before conditionally executing CALL.
Both cells occupy distinct 64-byte slots after the three completion cells
in the existing CSF_EVENT BO. Later entries retain this guard even without
new explicit waits. CPU prevalidation and output callbacks refresh done and
payload before accepting completion. Semaphores owned by a queue that used
imports stay on their CPU callback: a plain foreign seqno wait cannot carry
the import error. No ERROR_BARRIER is emitted on guarded entries.
Import-bearing output signals also omit raw GPU export addresses: their
`sync_file` export waits for the error-checking CPU callback, including
zero-target signals. This export may block; ordinary non-import exports keep
the asynchronous CQS path. A fresh review exposed the bypass, and three
new export regressions failed before the fix (the non-import control passed).

The expanded integration suite has 38 methods, including two using the real
v11 packer/builder, with six foreign waits plus the import guard. Normal
entries measure at most 384 bytes, diagnostic entries 432 bytes, below the
unchanged 512-byte limit. Guarded diagnostics omit optional pre/post-CALL
breadcrumbs but retain completion diagnostics; the first real-builder
diagnostic test reproduced overflow before that adjustment. Builder
temporary storage is finalized after recording the entry size.
All 95 related host tests passed (integration, checked teardown, snapshot,
bridge, WAIT_ANY and native-harness regressions).

These are source-extracted host checks, not a full Mesa/ABI build or hardware
execution. Cross-cell publication, real negative-fence GPU behavior and
firmware termination remain unqualified; gate 1.3 stays BLOCKED. Nothing
selects 006 in a build, and the active default series remains 002-005.

## Default release series (approved 2026-11-24)

The user approved promotion of the complete 002-005 series after reporting
the Nyushu comparison below. G615 Mesa 27 preparation now applies the main
series followed by 002, 003, 004, and 005 by default, in the same fixed order
as the previously built opt-in candidate. The directory name is historical.
Use a fresh checkout at the pinned Mesa commit:

```sh
./scripts/apply-patches.sh --profile g615-v11-csf \
  --mesa /path/to/clean/mesa
MESA=/path/to/clean/mesa ./scripts/build-android.sh \
  --profile g615-v11-csf --ndk /path/to/android-ndk
```

The build command consumes the prepared tree; it does not apply patches
itself. Do not apply the preparation command to an already patched tree.
Preparation rejects other profiles, excludes historical 001, and retains
the offset/fuzz rejection gate. New experimental patches are not included
automatically. Both supplied patches match the consolidated code; only
hunk coordinates were refreshed for strict replay.

The prior G615-only candidate replay applied all 196 patches without offsets
or fuzz and passed the Android build and focused backoff/provenance tests.
Selection tests now expect the same 002-005 inputs with and without
`--with-kbase-sync`; unsupported profiles still fail explicitly. No build,
test suite or device run was repeated for this promotion, as requested.

The user subsequently reported 20 FPS at 0.5X. This is a user-observed
result, not a new instrumented capture or proof that 003 caused the gain.
The prior shutdown failure remains an open acceptance limitation. Promotion
does not certify its resolution or the absence of other regressions.
No device selection or resolution is changed by this consolidation.

For the Mesa 27 profile at `13baeb70c0`, apply
`002-android-release-queue-mesa27.patch` after the profile patches, including
Android 018 (the port of historical 0178). Patch 002 is an alternative to
001; do not apply both. Its updated revision retains backend-specific
callback selection, adds address-based cross-queue GPU waits, rejects
external sync-file/non-CSF payloads during peek, skips already-retired
producer seqnos, and stages per-subqueue wait updates transactionally. Patch
003 coalesces up to 64 deferred `MEM_SYNC` operations on the stack and falls
back to direct uncoalesced emission if heap allocation for larger batches
fails. Patch 004 closes `sync_file` waiter lifetime gaps when pending payloads
resolve, fail, reset, or are replaced. None of these patches require the
historical Kraid overlay.

Patch 005 replaces the `WAIT_ANY` yield loop with an exponential sleep from
50 us to 1 ms, clamped to the remaining absolute timeout. Interrupted sleeps
recheck syncs and the deadline; other sleep errors are logged and propagated.
Immediate success, zero/expired timeout and `WAIT_ALL` behavior are preserved.
Host tests compile the wait function with deterministic clock/sync stubs;
they do not establish device CPU, clock, temperature or runtime correctness.
The user-reported CPU/thermal comparison is recorded below; it is not an
independently captured device gate.

The legacy variant label `kbase-sync-002-004` is retained for compatibility.
The legacy flag is optional and selects that label with the same ordered
inputs as `default`. Both manifests include 002-005 and their SHA-256 hashes;
old manifests are not valid provenance for this candidate. The Android build consumes the prepared
tree and does not accept `--with-kbase-sync`.

All four patches are included in the default G615 patch series. Do not apply
them again to a tree prepared by `scripts/apply-patches.sh`.
For historical manual preparation, verify the base, then check and apply:

```sh
git -C /path/to/mesa apply --check /path/to/002-android-release-queue-mesa27.patch
git -C /path/to/mesa apply /path/to/002-android-release-queue-mesa27.patch
```

For the historical Mesa 26 tree, use an isolated prepared tree with the G615
Kraid experimental overlay instead:

```sh
git -C /path/to/mesa apply --check /path/to/001-android-release-queue.patch
git -C /path/to/mesa apply /path/to/001-android-release-queue.patch
```

### User-reported Nyushu comparison and release approval

On 2026-11-24 the user reported testing and approval of patch 005 and explicitly
approved promoting all of 002-005 to the principal release series:

| Metric | Baseline (`sched_yield`) | Patch 005 (`nanosleep`) |
|---|---|---|
| Process CPU | 364% | 148% |
| Kernel time (`%sys`) | 227% | 121% |
| Idle CPU (`%idle`) | 168% | 479% |
| Swap / ZRAM in use | 2.64 GB | 1.71 GB |
| Internal SOC / GPU temperature | 65.0-66.4 C | 50.8-51.2 C |
| External SKIN temperature | 40.3 C | 35.3 C |

The reported process CPU reduction is approximately 59%; kernel and idle
changes are -106 and +311 percentage points, respectively. These are
user-supplied observations, not measurements collected during this promotion.
Exact device/UAPI, binary hashes, sampling duration and raw logs were not
provided with the comparison; it does not establish glibc or other-device
performance, general stability, or causality for the swap/ZRAM change.
Existing binaries and package metadata are preserved, not rebuilt or
relabelled with the new source provenance. A future publication requires a
new immutable release and matching binary/package provenance.

Kbase uses a CPU-backed sync type, not DRM syncobjs. The patch leaves the
DRM callback unset for Kbase, so the common Android native-buffer release
path submits its semaphore waits and signal through the queue. DRM backends
retain the original callback. The Kraid default is unchanged.

On the Moto G86 in shell, the previous driver failed `anb_release` with one
and two wait semaphores in two runs each (`VK_ERROR_UNKNOWN`). The candidate
passed both cases twice with valid, signaled sync-file descriptors. This
does not validate the Android system loader, app-UID release, visible frames,
other Kbase devices or general synchronization semantics. In an isolated
app UID, native-buffer image creation failed before release for both the
previous driver and this candidate; the candidate logged an inaccessible
MediaTek mapper and unavailable layout metadata. The candidate also
passed 54 separate compute, linear IDVS, and offscreen regressions in the
isolated app, but those tests do not exercise native-buffer release. See
[the test documentation](../../tests/README.md) for reproduction.

## Mesa 27 Eden import test (2026-11-18)

The candidate includes Android 018 and experimental 002. The Android G615
build and static binary validation passed. Shell `anb_release` tests with one
and two wait semaphores returned valid, signaled sync-file descriptors.

The development package was imported through Eden's GPU driver manager as
`PanVK-release-sync-test-20261118.adpkg.zip`. Selection was saved by leaving
the settings screens. The configured package path and extracted library
were checked; the library SHA-256 matched the packaged build:

```text
612b49cde32cdc3d6245c9b83ae54590142c7db9d7ea269b21e726c697b6f291
```

Resident Evil 0 reached `EmulationActivity` with Kbase initialization logged
under PIDs 19459 and 20941. Neither PID logged the former
`QueueSignalReleaseImageANDROID failed`, DRM syncobj export, or
`GetMemoryFdPropertiesKHR failed` signatures. The second shared game log
continued through 155 seconds. This is not a frame-correctness pass:
the captured emulation screen was black, and both processes subsequently
exited. Android exit-info reported `UNKNOWN`, status 0, without an
identified native abort or an established cause in this capture.

The shared log still reports Vulkan validation errors, including query
render-pass scope and provoking-vertex pipeline state. Their causal
relationship to the black screen or exit is not established. Do not treat
the missing release errors as proof that visible rendering is fixed.

### Follow-up: playable scene and performance

In the subsequent user-driven run on the same device, the initial train
scene rendered visibly with characters and environment present. The
extracted driver retained the SHA-256 above. PID 4114 stayed active during
the measurement. This supersedes the earlier black-screen observation for
that scene; it is not a general rendering-correctness or stability pass.

The overlay showed 8.7 FPS. During 01:37, 56 SurfaceView `queueBuffer`
reports had a median of 8.975 FPS (range 5.54–9.23). These are producer
rates, not instrumented GPU frame durations. A later 30-sample GED capture
reported median GPU utilization of 96%, with a range of 0–100%.
Reported GED frequency was 1,047,000 kHz in 19 samples and lower in the
others. CPU sampling over approximately 60 seconds showed the busiest
`VulkanWorker` thread averaging 38.1% of one core. Thermal service reported
status 0, without a thermal throttling indication. The memory snapshot
contained approximately 2.79 GiB total PSS and 649 MiB swap PSS.

These measurements identify GPU-side load as the primary performance
investigation target, not CPU saturation or observed thermal throttling.
They do not distinguish shader execution, bandwidth, synchronization
overhead, or driver submission costs. There were no prior native-buffer
import, DRM syncobj export, or release-image failure signatures under
PID 4114 in the captured interval.

The user then reduced resolution from `Res1X` to `Res3_4X` and restarted
the game (PID 17940), retaining the same driver hash. Among logged settings,
resolution was the only changed value. The same train scene remained visible.
Over approximately 65 seconds, 61 SurfaceView reports had a median of
10.32 FPS (range 9.84–10.65), a 15% increase over the preceding median.
Thirty GED samples had median GPU utilization of 94%; the busiest
`VulkanWorker` thread averaged 47.5% of one core. Thermal status remained 0,
and the prior import/release error signatures were absent.

Both runs reported the Khronos Validation Layer attached. Thus these are diagnostic, not
validation-disabled performance baselines. The modest resolution scaling
shows a pixel-cost contribution but does not establish a purely
fill-rate-limited workload. Isolate validation-layer overhead in a separate
same-scene comparison before attributing the remaining cost to driver code.

### Graphics debugging disabled

The effective Eden switch is Settings > Advanced Settings > Debugging >
Graphics debugging (`Renderer.debug`), not
`Debugging.perform_vulkan_check`. The latter remained true after disabling
graphics debugging. The driver build already used release, optimization 3,
and `b_ndebug=if-release`; disabling driver assertions was not required.

After disabling graphics debugging through the UI and restarting, PID 21566
had no Khronos Validation Layer mapped. The log confirmed
`Renderer.debug: false` and `Res3_4X`. The visible train scene showed
16.2 FPS. During a 65-second capture, 62 SurfaceView reports had median
15.99 FPS (range 14.79–16.90). GPU utilization median was 97% across
30 samples; thermal status was 0. No release-image failure, device-lost,
or fatal-signal signatures occurred in that capture. The driver hash
remained unchanged.

This rate is 54.9% above the earlier 10.32 FPS measurement, but the
comparison is not a controlled estimate of validation overhead:
GPU accuracy, GPU unswizzling, and anisotropy also differed from that
earlier run. Those three settings already differed in the running session
before this intervention; only `Renderer.debug` changed from the
immediately preceding session, for which a matching FPS capture is absent.
The retained configuration uses High accuracy, GPU unswizzling enabled,
and X8 anisotropy. A 1X performance recovery and the separate shutdown
hang remain unverified. No new driver performance patch was applied.

The subsequent 1X run retained graphics debugging disabled, High accuracy,
and X8 anisotropy. A 65-second capture contained 61 SurfaceView reports:
median 11.42 FPS, range 10.31–12.60. The screenshot showed 10.6 FPS.
GED utilization median was 98% across 30 samples; thermal status was 0.
No Khronos Validation Layer was mapped, and no release-image failure,
device-lost, or fatal-signal signatures occurred during the capture.
The camera and character position differed from the preceding 0.75X
screenshot, so these captures are not a strict resolution-only A/B.
The reported historical minimum of 15 FPS at 1X was not recovered.

## Updated 002: cross-queue waits

The user-supplied update replaces same-queue-only seqno waits with
address/seqno pairs, allowing the consumer GPU queue to wait on producer
queue completion without a CPU completion wait. Duplicate addresses merge
by maximum seqno; capacity overflow retains the CPU fallback.

Integration corrected malformed hunk counts, added the new argument to
subqueue initialization, and retained the original release callback fix.
Two conservative guards were added: cross-queue empty submits retain CPU
waits because they emit no stream to carry a GPU wait, and pending payloads
without nonzero GPU targets retain CPU waits (including imported sync-file
payloads). The attachment itself was not edited.

The final candidate is named `PanVK-release-sync-r2-safe-20261118`.
It was built, packaged as ADPKG, imported through Eden, and selected with
the selection saved before launch. The extracted library, local build,
and ADPKG library all matched:

```text
6798588336613f108c2e2893059a3b84a23da9ceaddedeef3242a29f5d91b858
```

Validation:

- Android release build and static binary validation: PASS.
- ADPKG ZIP integrity and embedded library hash: PASS.
- Four Android 018 / historical 0178 host regression tests: PASS.
- Shell native-buffer release with one and two wait semaphores: PASS.
- Shell fence, binary semaphore, repeated submission, queue/device idle,
  and compute magic readback: PASS.
- Twenty bidirectional cross-queue chains with GPU work and twenty empty
  cross-queue consumer submits: completed with PASS.
- Eden PID 9727, 1X, graphics debugging off: scene visibly rendered.
  No logged setting differed from the preceding 1X baseline.
- Sixty-five seconds, 61 SurfaceView reports: median 12.20 FPS,
  range 8.72–13.57, mean 11.80. Previous 1X median was 11.42 FPS.
  The median is 6.8% higher, but this is not proof of a general speedup;
  the sampled minimum was lower and cameras differed.
- GPU utilization median: 99% across 30 samples. Thermal status: 0.
  No prior import/release errors, ring emission failures, device-lost,
  or fatal-signal signatures occurred during the gameplay capture.
- Normal "Exit emulation" returned to MainActivity. The log recorded
  pipeline-cache serialization and GPU logging shutdown completion.
  A subsequent native stack dump contained no NativeEmulation or
  VulkanWorker threads and no OnTerminate/ShutdownMainProcess wait.
  However, the guest PANIC 2010-0212 and a host_memory.cpp assertion
  were still logged; this is not an error-free shutdown claim.

The previous working ADPKG remains available for rollback. The candidate
remains opt-in; it has not recovered the historical 15 FPS minimum at 1X.
Unsignaled external sync-file imports, wait-list overflow stress, broader
games, and long-duration stability remain outside this validation.

## Experimental 003: deferred MEM_SYNC coalescing

Apply `003-kbase-coalesce-mem-sync.patch` after the updated 002. It is
opt-in and is **not approved as regression-free**. It sorts pending
operations by BO and start, then coalesces overlapping or adjacent ranges
of the same operation type. Coherent BOs still bypass MEM_SYNC.

The supplied patch required corrected hunk lengths, a final newline,
and the `util/stack_array.h` include. Integration also frees the temporary
array on success and ioctl failure, and logs allocation failure. To avoid
widening invalidations into gaps or changing operation types, this version
does not merge across a 4096-byte gap or promote mixed operations to
flush-and-invalidate. The read-only attachment was not modified.

The resulting `PanVK-release-sync-r3-20261118.adpkg.zip` was imported,
selected, saved, and launched through Eden. The extracted library matched
the local build and package identity:

```text
dbd9dd2cb9a6b0f194964c4250f96a468f8b5114c3e6f3ed91454d244848f661
```

Validation on 2026-11-18:

- Android build/static validation: PASS.
- Host coalescing harness: PASS. Covers empty/single batches, coherent BO
  bypass, unsorted overlap/adjacency, distinct BOs/types, gaps, input
  preservation, 4096 operations, allocation failure, ioctl failure, and
  temporary storage cleanup.
- Four historical 0178 / Android 018 host tests: PASS.
- Device ANB release (one/two semaphores), same-queue sync, compute
  readback, and bidirectional cross-queue tests with GPU work and empty
  consumers: PASS.
- Eden PID 28314, 1X, graphics debugging off: visible train scene,
  unchanged logged settings from 002-r2-safe. No Khronos layer mapped.
- Sixty-five seconds, 61 SurfaceView reports: median 12.39 FPS,
  range 10.98–13.54, mean 12.42. The previous median was 12.20 FPS.
  The 1.6% median increase is not evidence of a significant speedup.
- GPU utilization median 98%, frequency 1,047,000 kHz in all 30 GED
  samples, thermal status 0. No MEM_SYNC, native-buffer import/release,
  ring emission, device-lost, or fatal-signal failures in the gameplay
  capture. No device ioctl-count reduction was measured.
- **Exit validation failed.** Normal Exit emulation remained in
  EmulationActivity. Two native snapshots retained the shutdown wait in
  `Service::VI::Container::OnTerminate` / `ShutdownMainProcess`.
  The shared log ended after guest PANIC 2010-0212 and guest backtrace.
  The similar hang existed before 003, so these captures do not prove
  that coalescing caused it. Nevertheless this fails the acceptance gate;
  002-r2-safe had completed the previous exit test.

With user authorization, the stuck process was force-stopped and the
previous 002-r2-safe ADPKG was selected again through Eden. Launch verified
the restored library hash `6798588336613f108c2e2893059a3b84a23da9ceaddedeef3242a29f5d91b858`.
The 003 sources/build and candidate package remain available for diagnosis,
but 003 is not active in Eden and is not in the default patch series.

## Manual validation: consolidated 002-004 (2026-11-19)

After consolidating patches 002, 003, and 004, the user reported two manual
tests across two different emulators. Neither test reproduced the prior
display freeze with audio continuing, and open file descriptors remained
stable instead of growing toward the previously observed 8,000. The reported
average was about 300 process fds, with zero `sync_file` fds observed.

The user also reported recovering the prior 1X performance baseline of about
15 FPS and reaching approximately 30 FPS at 0.5X. These are user-observed
results; per-run logs, exact emulator identities, measurement intervals, and
FPS sampling details were not attached. Treat the results as promising manual
evidence, not a controlled benchmark or broad stability certification.
This report supersedes the earlier statement that 003 was not active for
device validation; the consolidated 002-004 candidate was manually tested.
The experimental patches remain opt-in and are not included in the default
release series.
