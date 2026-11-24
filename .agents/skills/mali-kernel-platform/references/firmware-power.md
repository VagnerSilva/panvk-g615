# Firmware, energy and recovery observations

Development starts at the [initialization/notification/probe map](implementation.md#use-the-known-edit-sites-first).
Preserve userspace initialization/error cleanup and implement only supported
observations; unknown reset/firmware contracts block that feature, not all work.

## Scope and known limits

Only observe already accessible interfaces for the identified Moto/context.
Do not infer firmware identity from CSF 1.21 or power policy from successful
submission. Kernel, firmware and userspace are different layers.
See [operational consolidation](../../../../docs/engineering/mali-kernel-platform/TECHNICAL_CONSOLIDATION.md#operational-boundaries-and-backlog)
and [central layer separation](../../mesa3d-mali-expert/SKILL.md).

| Topic | Current evidence boundary |
|---|---|
| Firmware version/hash/source | UNKNOWN unless a trustworthy matching record is obtained |
| Kernel/DDK internals | Matching Moto source/details not recovered; userspace ABI is not handler proof |
| DVFS, governor, thermal transitions | Not measured in this investigation |
| Suspend/resume | No matching Moto gate recovered |
| Reset/recovery | No qualified fault/reset/recovery result |
| Stability | Narrow historical workloads, not general recovery or endurance proof |

## Safe future observations

After explicit device/action approval, reuse existing logs first. Read only
identified read-only accessible properties/versions/sysfs entries. Record
workload times, charging/screen state and available thermal observations;
unknown or denied paths stay unknown, without automatic root requests.
Filter logs to the test process/window; do not clear buffers or expose unrelated
data. Do not enumerate/read arbitrary debug interfaces.

Do not write firmware, clocks, governor, runtime-PM, reset/debugfs controls or
restart services to test a hypothesis. Stop new submissions on timeout,
device-lost, fault, critical thermal state or unresponsive system. End only the
authorized isolated process if safe; otherwise require authorized manual
recovery. A reboot is not proof of GPU recovery.

Unknown internals do not block generating a limited skill; they block specific
firmware/power/recovery claims. Use
[device validation](../workflows/device-validation.md), and report every
unexecuted dimension through [validation](validation.md).
