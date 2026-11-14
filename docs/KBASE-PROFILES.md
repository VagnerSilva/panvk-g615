# Kbase profiles

Selection key (minimum): `pan_arch + gpu_id + frontend + kbase_uapi`.
Preferred: `<arch>-<gpu-id>-<frontend>-<uapi>`. Never select from the Android
marketing GPU string.

Primary: `g615-v11-csf` — Poco X6 Pro, Dimensity 8300-Ultra, G615 MC6
(`Mali-G615 6 cores r1p3 0xB8A3`), CSF, `/dev/mali0` mode `crw-rw-rw-`.

## G615 tiler defaults (patch 0177)

All kbase Mali-G615 devices use incremental rendering **off** and tiler
heaps with **10 initial / 400 maximum 1 MiB chunks**, for every application.
Selection uses the Mesa product ID `PAN_PROD_ID(11, 8, 3)`, regardless of
core count or revision; G715 (`PAN_PROD_ID(11, 8, 2)`) is not included.
Other GPUs and the panthor path keep their existing defaults.

Explicit `PANVK_KBASE_TILER_IR=0`/`1` and
`PANVK_KBASE_HEAP_CHUNKS=<initial>[,<max>]` override these defaults
independently. For example, `PANVK_KBASE_TILER_IR=1
PANVK_KBASE_HEAP_CHUNKS=4,400` restores the previous G615 defaults.
Settings are resolved per physical device and shared by queue creation,
fragment commands, and initial, spare and renewed heaps. Logs report the
resolved IR mode and chunk counts.

This workaround follows a user report: Factorio in Pocket Foundry lost the
GPU on G615 MC2 with driver 26.3.1, while IR off and `10,400` ran for nearly
five minutes and exited normally. G615 MC6 reportedly had similar speed
with either configuration. That is not a long-duration stability test.
With IR off, exhausting the maximum heap can still cause `DEVICE_LOST`.
The published 26.3.1 binary does not contain patch 0177.

Probe (`tests/kbase-probe/`) captures before any Vulkan: SoC/GPU model/ID,
pan arch, `/dev/mali0` existence + O_RDONLY/O_RDWR + errno (ROOT/SHELL and
target-app UID separately), Kbase UAPI, DDK/module version if safely readable,
JM/CSF, shader-core mask, coherency, memory, CSF interface properties.
A driver that only opens `/dev/mali0` as root is not app-loadable.
