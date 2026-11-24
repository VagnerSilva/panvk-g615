# Workflow — platform discovery

## When and prerequisites

Start every kernel/platform investigation here. Read [SKILL.md](../SKILL.md)
and [architecture](../references/architecture.md). Repository inspection is
read-only; device access is a separate action requiring explicit approval.
Do not assume a clean checkout or that the build profile describes Moto.

## Sources and steps

1. From the repository root, record status, source pin and declared inputs:

   ```sh
   rtk git status --short
   rtk git branch --show-current
   rtk git rev-parse HEAD
   rtk git -C work/mesa rev-parse HEAD
   rtk git -C work/mesa status --porcelain=v1 --untracked-files=all
   rtk bypass cat sources.lock
   rtk bypass cat work/mesa/VERSION
   rtk bypass python3 scripts/compute-patch-series-id.py --profile g615-v11-csf
   ```

   Missing Mesa/tools are BLOCKED for those checks; never fetch/reset originals
   to make them pass. Compare the computed hash without changing the lock.
2. Read the profile and exact manifest/variant. Distinguish input hash from
   selected/applied patches and binary. Preserve all diffs and untracked inputs.
3. Reuse [current evidence register](../../../../docs/engineering/mali-kernel-platform/EVIDENCE_REGISTER.md)
   and matching logs. Record Moto/GPU/PAN_ARCH, Android or glibc, ICD
   hash/Build ID and observed UAPI; do not fill gaps with MC6 data.
4. For future authorized device collection, identify process context, node
   access, actual page size and known kernel/firmware fields using already
   reviewed read-only procedures. For glibc also identify guest/libc, loader,
   JSON resolution, namespace and display/socket access.
5. Select the dependent domain workflow. Missing original F0–F5 map remains
   unknown; do not invent phase completion or repeat earlier investigations.

## Evidence, gates and stop

Deliver a platform/input/binary/context tuple with source locators, dates,
unknown fields and the next selected workflow. Use the
[validation contract](../references/validation.md).

PASS discovery means identities needed for the next action are established,
not device support. Input mismatch is FAIL provenance; missing mandatory
identity/access is BLOCKED. Never execute a test with unresolved target,
binary, libc or authorization.
On a device/namespace denial, stop without privilege/policy changes.
See [security](../references/security.md).

## Authorization boundary

This workflow does not authorize ADB, probing, installs, transfers, mounts,
cleanup, builds, patches or commits. Request explicit action/context approval
only if a new observation is necessary; existing unknowns can remain documented.
