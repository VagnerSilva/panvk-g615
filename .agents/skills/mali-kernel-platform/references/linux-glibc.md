# Linux/glibc in the Android handset

For userspace capability work use [recipe D](implementation.md#recipe-d--implement-an-observable-platform-capability)
and the mapped probe/guest/loader components. Compile/test each claimed libc
separately; source changes may be prepared while runtime remains unqualified.

## Scope

Only glibc userspace in a chroot on Moto; not Linux-native, Panthor or PRoot
qualification. Source: [G615 specification](../../../../docs/superpowers/specs/2026-11-21-g615-only.md:3).
Same kernel/GPU does not establish equivalent libc, loader, ABI, access or WSI.

## Separate prerequisites

Identify guest distribution and real libc, effective UID/groups/SELinux context,
mount namespace, `/dev/mali0` visibility/access, loader/interpreter and target
dependencies. A wrapper named Alpine/chroot does not establish glibc.

The chain is glibc app → glibc Vulkan loader → glibc ICD plus
`panfrost_icd.aarch64.json` → Android Kbase. Resolve JSON/library paths in the
guest filesystem, not the host. Do not load the Bionic ICD in place of glibc.
Sources: [architecture](../../../../docs/ARCHITECTURE.md:17),
[glibc build](../../../../scripts/build-glibc.sh:86).
Build commands with a hardcoded guest/root wrapper do not discover or authorize
the user's environment. Route build changes to
[build validation](../../panvk-build-validation/SKILL.md).

For X11/Wayland, identify server/compositor, socket visibility and client
authorization. DISPLAY/WAYLAND_DISPLAY alone do not establish access.
Headless compute/offscreen cannot qualify presentation. No automatic bind
mounts, copied credentials or socket-permission changes.

## Evidence and remaining gates

Moto runtime qualification was not recovered in the consulted evidence.
Profile `glibc: pass`, placed-map CTS and
[old glibc runtime](../../../../validation/g615-v11-csf/beta3-phase8-glibc-runtime-2026-09-19.txt:1)
concern MC6/history, not Moto or the current series.

Require a separate per-ABI binary/manifest/context and selected functional
gates; record missing prerequisites as BLOCKED, not a negative compatibility
result or inherited Android PASS.
Use [discovery](../workflows/platform-discovery.md),
[device validation](../workflows/device-validation.md) and
[memory/sync audit](../workflows/memory-sync-audit.md).
