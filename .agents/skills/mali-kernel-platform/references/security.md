# Operational security and access boundaries

## Scope

Device access, process identity, namespaces, permissions and safe operation.
This reference is not an exploitability assessment or authorization to change
security policy. Follow [AGENTS.md](../../../../AGENTS.md).

## Evidence and invariants

- [Historical Moto context evidence](../../../../docs/engineering/mali-kernel-platform/TECHNICAL_CONSOLIDATION.md#android-versus-linuxglibc)
  distinguishes an untrusted app from a root/KSU control. The control's exact
  identity at its original run was not captured; never call it ordinary shell.
- Unix mode, successful root open or profile MC6 access does not establish
  Moto app access. GPU-node, mapper service and linker namespace access are
  independent gates.
- A chroot changes filesystem view, not kernel/firmware or automatic SELinux
  access. Identify actual UID/groups/context and mount namespace separately.
- Identify the loaded ICD and private-file/marker precedence before testing.
  Never overwrite another experiment's files or assume a ZIP hash identifies
  the library loaded.

## Authorization and stopping

Read-only repository inspection is distinct from device connection, execution,
installation, transfer, mounting, cleanup or source changes. Get explicit
approval for the latter actions and preserve all existing data.

On access/mapper/linker/socket denial, preserve the first error and stop that
gate. Do not chmod/chown, change SELinux/linker policy, escalate to root or
open display sockets to everyone to turn an app failure into PASS.
Do not extend a cookie-writing probe to external buffers.

Use a total timeout with a reviewed target-process stop mechanism. Host/ADB
timeout may leave remote work alive; do not use a long detached CTS campaign
runner as a bounded diagnostic. Stop only the identified authorized PID/package,
never by name or broad process matching. No automatic reboot/GPU reset.
Minimize logs; omit serials, full fingerprints and unrelated process/user data
from summaries. Cleanup only exact objects created by the authorized test.
Use [discovery](../workflows/platform-discovery.md) and
[device validation](../workflows/device-validation.md).
