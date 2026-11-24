# Workflow — bounded device validation

## When and prerequisites

Use only when a new observation is necessary after existing evidence review.
This workflow does not authorize hardware execution. Complete
[discovery](platform-discovery.md); obtain explicit approval for Moto, platform,
process context, binary, exact test, duration and stopping/cleanup scope.
Without approval: NOT EXECUTED. Missing safe prerequisites: BLOCKED.

Read [validation](../references/validation.md),
[security](../references/security.md), and the relevant
[Android](../references/android.md) or [glibc](../references/linux-glibc.md)
reference. Confirm that tests/skills exist; do not invent a runner.

## Sources and steps

1. Identify ICD hash/Build ID/manifest, selected variant, actual loaded path,
   UAPI/page and process context. Check app-private marker precedence or
   glibc loader/JSON/guest resolution before choosing a workload.
2. Select one relevant [existing test](../../../../tests/README.md), one small
   workload and a total timeout that terminates the actual isolated target.
   No automatic install, copy, mount or root wrapper; approve those separately.
3. For Android sync_fd or sync_wait_signal, follow the
   [documented test modes](../../../../tests/README.md:168)
   in an approved isolated app. Require successful queue submits, valid
   sync-file info, bounded poll and fence completion. These gates do not test
   rendered content, AHB, WSI, interprocess stress or every lifetime path.
4. For glibc pending-fence lifetime, use the prerequisites and exact outcomes in
   [memory/sync audit](memory-sync-audit.md). For content or presentation,
   choose the documented relevant gate separately; headless is not WSI.
5. Keep driver-owned WSI, external AHB and private ANB release independent.
   Do not rerun external-AHB app import merely because this workflow exists:
   its historical FAIL is deferred until user decision or release requirement.
6. For [firmware/power](../references/firmware-power.md), use only approved
   read-only observations; do not introduce suspend/reset/fault/clock writes.
   A limited observation cannot qualify endurance, DVFS or recovery.
7. Capture first error, exit/result, expected versus actual output, hash/context
   and bounded logs. Stop on the first failure before another variable/run.

## Gates, stopping and delivery

PASS applies only to the executed case on the recorded tuple. Enumeration,
command launch or return code without the required result is insufficient.
Report build, binary structure, execution, stability/performance and audit
independently; old reports remain HISTORICAL_REPORT.

Stop new submissions on wrong readback, FD growth, unexpected timeout,
total-deadline expiry, access denial, device-lost/fault, thermal/data risk or
unresponsive system. A fixture's explicitly expected timeout and serial wait
are test stages, not permission to retry a failed workload. Stop only the
approved isolated PID/package if safe. No broad kill, policy change, reset,
reboot, firmware/governor modification or automatic long retry.
If the target cannot be stopped safely, report BLOCKED recovery and request
authorized manual action; do not claim recovery from a reboot.

Deliver test command/procedure, limits, target identity, per-gate results,
minimal logs, unexecuted paths and next bounded action. Cleanup only exact
objects created in the approved run; preserve preexisting private ICDs/apps,
markers, logs, user files and original sources.
