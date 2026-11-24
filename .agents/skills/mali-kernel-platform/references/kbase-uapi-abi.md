# Kbase UAPI and ABI

For a compatibility edit use [recipe C and selector/header targets](implementation.md#recipe-c--modify-csf-management-without-changing-its-abi).
Preserve packed requests and guards and test fallback/cache/error paths;
do not send raw requests to rediscover documented layouts.

## Scope and source of truth

Use the consumed
[ioctl header](../../../../patches/kbase-common/files/include/drm-uapi/mali_kbase_ioctl.h:28)
and exact downstream call sites, not similarly named reference headers.
Patch locators refer to patch-file lines, not final applied-source line numbers.
The [targeted consolidation](../../../../docs/engineering/mali-kernel-platform/TECHNICAL_CONSOLIDATION.md#kbase-uapi-and-csf)
records the 2026-11-23 inspected state; reverify after input changes.

Record ioctl type, direction, nr, encoded size, alignment, field offsets,
reserved fields, widths and version guard. A name or version match alone
does not prove vendor-kernel compatibility.

## Static predictions for reported CSF 1.21

| Operation | Source prediction |
|---|---|
| Group create | 32 → 112 → 40-byte layouts, nr 42 then 58 |
| Heap init | 16 → 24-byte layouts, nr 48 |
| Allocation | MEM_ALLOC_EX nr 59 / 64 bytes; restricted MEM_ALLOC fallback |

Source: [110 selectors](../../../../patches/csf-v11/110-select-kbase-csf-uapi-layouts-and-16k-pages.patch:450)
and its lines 524–558. These are comparators, not observed Moto results.
Group/heap fallback only on EINVAL/ENOTTY; accepted layout is cached.
Do not force fallback after ENOMEM, EPERM or EACCES. EINVAL may reject fields,
not merely size. For 1.21, the fault-report-enable guard remains false.

## Page and libc boundaries

[110 page handling](../../../../patches/csf-v11/110-select-kbase-csf-uapi-layouts-and-16k-pages.patch:287)
maps three CPU pages for USER_IO, input `+page`, output `+2*page`.
Use the BIND cookie directly; do not re-scale it or treat it as GPU VA.
CPU page size, GPU MMU granule and firmware-interface version are different.
[237](../../../../patches/csf-v11/237-kbase-exec-jit-and-ion-compatibility.patch:64)
carries shared EXEC-before-JIT and page calculations without requiring JM.

AArch64 Bionic/glibc should be checked independently for sizes, alignment,
pointer/off_t widths and dependencies; same kernel does not certify both builds.
Historic host assertions and G57 JM tests are not Moto CSF/16 KiB evidence.
Matching Moto kernel/DDK source, accepted layouts and page/GLB facts remain
unknown where absent. Do not invent a compat handler.
Use [UAPI audit](../workflows/uapi-audit.md).
