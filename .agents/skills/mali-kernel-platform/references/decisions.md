# Decision matrix for development

Use this matrix before choosing a solution; investigate only a missing fact
that prevents the requested safe change. Sources:
[approved scope and consolidation](../../../../docs/engineering/mali-kernel-platform/TECHNICAL_CONSOLIDATION.md),
[contract record](../../../../docs/engineering/mali-kernel-platform/audit/SKILL_AUDIT_CLOSURE.md),
[patch policy](../../../../patches/README.md).
The user authorized direct installation of this operational extension on
2026-11-23. It does not amend approved driver contracts or grant Mesa patch
application/hardware permissions.

| Classification | Existing decision/contract | Required action |
|---|---|---|
| Approved decision | G15/Moto G86 MC2, PAN_ARCH11; Android/Bionic and glibc chroot | Keep scope; do not infer PAN_ARCH15, Linux-native or additional support |
| Approved architecture | Kraid integrated; compiler and platform faults separate | Preserve compiler interfaces/selection; route actual compiler changes to Kraid |
| Confirmed interface contract | CSF versioned packing/guards and per-device layout cache | Preserve default order/zeros; only EINVAL/ENOTTY advance; a resource/access error is not ABI discovery |
| Documented memory contract with code discrepancy | SAME_VA cookie/mapping versus NEED_MMAP real GPU VA | Repair classification/ownership together using recipe A; do not say the old “011” is applied |
| Confirmed dependency boundary | Shared DMA-BUF backing, cache and sync_file are distinct | Preserve visibility/ordering/fences and ownership; FD-only success is not readback |
| Known limitation | Default waiter/poll/CLOEXEC defects and partial-KCPU contracts | Use recipe B; no fabricated cancellation/recovery or implicit fixes from patch presence |
| Known preexisting limitation | CSF bind cleanup can replace the initial errno with TERM's errno | Recipe C refactors compare observed baseline; record initial and delivered errors separately; save/restore needs a separate behavioral correction |
| Approved experimental policy | Sync 002–004 only opt-in `g615-v11-csf`, without 001 | Do not promote defaults or mix variants while comparing behavior |
| Known deferred failure | External-AHB app metadata inaccessible in documented ROM | Do not re-investigate automatically; block unsupported feature instead of bypassing mapper/SELinux |
| Rejected inference | Panthor VM_BIND, JM results or MC6 evidence imply Moto support | Do not reuse as compatibility proof; preserve only historical/boundary context |
| Rejected shortcut | Guess LINEAR/modifier, flags or GPU VA to suppress an error | Preserve real metadata/VA and explicit error; no cookie writes into external buffers |
| Real gap | Matching applied snapshot, target layout, kernel cancellation or new ABI unknown | Ask only for that prerequisite/evidence; block the affected change, not all development |
| Unvalidated hypothesis | Faster cache batching, safe recovery or universal coherency | State predicted invariant; controlled comparison required; no stability/performance claim without execution |
| Permission boundary | Patch preparation versus application, build/installation/device actions | Prepare isolated reviewable changes; obtain the separately required explicit approval |
| Editing workflow | Patches mandatory only for Mesa driver changes targeting `work/mesa/` | Edit skills/docs/scripts/tests/apps directly; retain scoped authorization and diff review without a non-Mesa patch step |

Do not reopen settled investigations to fill a generic matrix. If the requested
behavior already exists in the selected source, report a no-op with locators
and the relevant check rather than creating a redundant patch.
