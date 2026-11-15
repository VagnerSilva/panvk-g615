# Experimental Kbase Android release synchronization

This patch is opt-in and is not included in the default patch series or the
previously delivered ZIP. Apply it only to an isolated prepared Mesa tree with
the G615 Kraid experimental overlay. Verify the base, then check and apply:

```sh
git -C /path/to/mesa apply --check /path/to/001-android-release-queue.patch
git -C /path/to/mesa apply /path/to/001-android-release-queue.patch
```

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
