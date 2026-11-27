# Profiling collection by domain

## Common rules

First use logs and counters already available in the
[corresponding workload](benchmarking.md). Collect only from the authorized
process/time window, without uploads, automatic root access, or inspection
of third-party processes. Do not profile and run the baseline benchmark in
the same run: capture changes overhead; use a separate instrumented control.

Availability has three states: **confirmed in the identified run**,
**conditional, pending confirmation**, and **unavailable/UNKNOWN with a reason**.
Denied permissions, missing files, invalid values, or missing tools do not
become 0. `UNKNOWN` does not block valid wall timings, but blocks a hypothesis
that depends on that counter. Do not attribute energy consumption without a
valid electrical measurement.

| Metric | Source and collection | Availability/limit |
|---|---|---|
| Offscreen frame, wall latency | Workload/tess BENCH, BC `upload_wall_ms`, `wallA` | Implemented in the source; Moto execution remains conditional |
| Presented FPS/frame time | Existing workload capture of presentation intervals; separate present logs and visual confirmation | `BENCH present`, offscreen FPS, and present return values are insufficient |
| GPU timestamp | Queue-family properties plus BC queries; preserve `ts_bits`, `ts_period`, availability/wrap | Conditional; mandatory prerequisite gate in [benchmarking](benchmarking.md) |
| RSS/HWM | BC/tess `MEM` and `/proc/<PID>/status` | Process resident memory, not VRAM |
| Available memory/swap | `/proc/meminfo`, before/after and during the approved window | System-wide; correlation does not attribute bytes to the driver |
| Vulkan heap | BC `MEM heap_used_KiB`, `VK_EXT_memory_budget` dump | `heapUsage` is not RSS and does not establish bandwidth/occupancy |
| CPU/waits/submission | Workload timings; identified process and thread samples | Separate CPU recording from submit/fence; wall delta does not provide a breakdown |
| Frequency/temperature | Only an identified read-only Moto node and a documented reading with unit/origin | No Moto path qualified during this generation; UNKNOWN until confirmed |
| Utilization, occupancy, bandwidth, energy | Documented counter accessible for the device/context | Not established on the Moto; do not infer from a sysfs name |
| Firmware/CSF queues/groups | Identified error and wait logs, without new ioctls | No qualified firmware timestamp/counter; a wait alone does not attribute delay to a CSG |

## Minimal capture without an additional profiler

After approval, in the test shell/chroot, replace `<PID>` with the confirmed
PID of the **workload process**, not the `adb` wrapper. Confirm the process
UID, start time, and executable to avoid PID reuse.

```sh
date -u
cat /proc/<PID>/status
cat /proc/<PID>/stat
cat /proc/meminfo
```

Collect before/after snapshots with timestamps on the same time base and,
if needed, bounded samples during a longer workload. Preserve readings/errors.
`utime/stime` from `/proc/PID/stat` requires correct parsing of the `comm`
field (which may contain spaces/parentheses) and a tick unit confirmed with
`getconf CLK_TCK`; do not calculate percentages if tooling/parsing is
unavailable. Before/after RSS snapshots alone do not show a peak or leak origin.

For Android apps, filter logcat by PID/time window according to verified
`adb logcat --help` support; preserve runner tags and the first failure.
Do not use `logcat -c` or capture unfiltered global buffers. Collect kernel
fault logs only when already accessible and authorized; absence of logs does
not establish absence of faults.

## CPU and waits with simpleperf (optional and conditional)

Do not assume simpleperf is available on the Moto. After collection approval:

1. Check `command -v simpleperf`, `simpleperf --help`, and
   `simpleperf record --help` on the target; record version/help, attach/duration
   support, process access, and events. Missing/denied tool = BLOCKED profiler.
2. If the version confirms these arguments and permissions, capture **only**
   the authorized PID in a new isolated directory:

   ```sh
   simpleperf record -p <PID> --duration 5 -o ./cpu.data
   simpleperf report -i ./cpu.data
   ```

3. Confirm duration/exit status, actual samples, DSO/Build ID matching the
   handoff, and compatible symbols. Percentages without symbols or samples
   do not establish a cause; preserve UNKNOWN.
4. Separate recording, submit, wait, and present by thread/stack. Sleeping
   waits may not appear in on-CPU sampling: missing wait samples do not
   establish absence of blocking. Use wait start/end logs or an already
   qualified off-CPU trace; do not invent events.

Perfetto/AGI/HW counters have no established Moto recipe/configuration/permission
in this inventory. If needed, mark the gate BLOCKED until a short capture is
reviewed and authorized; do not install tools or create configurations with
assumed events.

## Analysis

Relate timings/counters to the same interval and clock; do not subtract a
GPU timestamp from a wall clock without established calibrated correlation.
`wall - GPU` includes CPU, waits, scheduling, and readback; it is not
automatically submission overhead. Use
[discriminating diagnosis](bottleneck-analysis.md); repeating a capture without
reducing uncertainty is not progress. Deliver data, interpretation, and the
next experiment, including unavailable metrics.
