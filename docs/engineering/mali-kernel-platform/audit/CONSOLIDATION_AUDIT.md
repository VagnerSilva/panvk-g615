# Independent consolidation audit

**Audit date:** 2026-11-21

**Mode:** Independent, read-only review by a separate agent.

**Scope:** Seven requested technical documents and executor autocheck;
selected cited source documents, worklogs 091/110/192, patch 110, patch 006,
and repository provenance.

The auditor did not edit repository files. Following this audit, the executor
made the remediations listed below. This report preserves the initial review
results and records the post-review status; it is not a substitute for missing
F0-F5 source artifacts or hardware validation.

## Audit results

| Requirement | Initial result | Post-review status | Summary |
|---|---|---|---|
| B1 — Integrity and completeness | PARTIAL | PARTIAL | Documents and evidence IDs were present. The audit-report link and some evidence links were corrected. F0-F5 completeness cannot be established because the phase map is absent. |
| B2 — Traceability | PARTIAL | PARTIAL | Mesa pin and patch-series ID match `sources.lock`. Patch 110 and WSI inventory citations were expanded; exhaustive source traceability remains incomplete. |
| B3 — Technical correctness | PARTIAL | PARTIAL | Kbase/Panthor and CSF/JM are distinguished. Test scope, 16 KiB validation, DMA-BUF coherency, and sync_file paths are clarified, but no current build/device validation was performed. |
| B4 — Evidence classification | PARTIAL | PARTIAL | Historical results and modified `work/mesa` are labeled as such. The distinction between G57 JM memory testing, CSF host/build checks, and untested 16 KiB behavior is explicit. |
| B5 — F0-F5 / F6-F12 coverage | BLOCKED | BLOCKED | F0-F5 definitions/handoffs are unavailable. F6-F12 are identified only as proposed work packages, not verified canonical phase scopes. |
| Executor autocheck | PARTIAL | PARTIAL | The missing link and overstatement in the link-check status were corrected. Autocheck remains partial because the underlying evidence gaps are unresolved. |

## Findings and remediation

### A-001 — Missing audit report target

- **Document:** `TECHNICAL_BASELINE.md`; initially also
  `CONSOLIDATION_AUTOCHECK.md`.
- **Problem:** The baseline pointed to a not-yet-created audit file.
- **Evidence:** The independent audit found the target absent.
- **Correction:** This report now exists at the linked path; the autocheck now
  records the audit as partial rather than pending.
- **Status:** Corrected.

### A-002 — Patch 110 test scope was ambiguous

- **Documents:** `EVIDENCE_REGISTER.md`, `COMPATIBILITY_MATRIX.md`.
- **Problem:** Earlier wording could conflate patch metadata, host assertions,
  a historical JM allocation test, CSF device validation, and 16 KiB behavior.
- **Evidence:** `worklogs/driver-remaining/110-kbase-csf-uapi-layouts.md`
  states host selector assertions and an Android build/binary validation;
  reports `memory.allocation.basic.*` 102/102 on TB336FU Mali-G57 v9 JM with
  an earlier 110 build, says the final-build rerun was skipped, and explicitly
  says none of the CSF paths ran on hardware and no 16 KiB device was
  available.
- **Correction:** Evidence E-012 and separate compatibility rows now state
  these scopes independently.
- **Status:** Corrected as a documentation distinction; reported tests remain
  historical and were not rerun.

### A-003 — DMA-BUF coherency and sync_file were too broadly summarized

- **Documents:** `EVIDENCE_REGISTER.md`, `FINDINGS_REGISTER.md`,
  `COMPATIBILITY_MATRIX.md`.
- **Problem:** Coherent imported memory could be misread as eliminating
  external sync_file waits.
- **Evidence:** Worklog 091 describes beta.9's missed sync_file waits and the
  beta.10 coherent dma-buf import path; worklog 192 separately describes
  imported sync_file/other-queue waits and sync_fd export, and explicitly says
  no hardware test was run.
- **Correction:** Evidence E-013 and the findings/matrix distinguish the
  memory visibility path from external fence completion and retain the
  historical/not-run labels.
- **Status:** Corrected as a documentation distinction; runtime behavior is
  still unverified in this task.

### A-004 — WSI inventory scope was insufficiently bounded

- **Documents:** `FINDINGS_REGISTER.md`, `INVESTIGATION_BACKLOG.md`,
  `EVIDENCE_REGISTER.md`.
- **Problem:** The evidence set did not support an exhaustive claim that no
  WSI compatibility evidence existed.
- **Correction:** FND-008 now states only that the reviewed evidence set does
  not establish a complete matrix. E-014 records that relevant WSI source and
  patch references exist but were not exhaustively traced or hardware tested.
  F11 is bounded to that gap.
- **Status:** Corrected as wording; full WSI investigation remains open.

### A-005 — F0-F5 coverage cannot be independently established

- **Documents:** `TECHNICAL_BASELINE.md`, `EVIDENCE_REGISTER.md`,
  `FINDINGS_REGISTER.md`, `INVESTIGATION_BACKLOG.md`.
- **Problem:** The supplied plan has no phase-by-phase definitions or artifact
  map. The workspace inventory cannot prove that phase records do not exist
  elsewhere.
- **Correction:** The documents state this limitation and mark F6-F12 mappings
  as proposed rather than canonical. E-011 records that the inventory is
  bounded; F6 asks for the missing definitions and handoffs.
- **Status:** BLOCKED pending authoritative phase artifacts.

## Provenance checked

The auditor reported root HEAD
`ef857062b90ee2448a5b812596ba8affb94ddcf6` and `sources.lock` Mesa commit
`13baeb70c066a9f82d2bcfb29f06e4865212affa`. It states the checked-out
`work/mesa` HEAD matches the pin but is extensively modified and has
untracked Kbase sources. It computed the `g615-v11-csf` patch-series ID and
found it matches `sources.lock`. No content from the modified tree was treated
as clean upstream or runtime evidence.

## Not verified

- No builds, unit/CTS suites, or device validation were rerun.
- Original raw device logs/screenshots were not independently inspected.
- No 16 KiB hardware behavior was validated.
- The F0-F5 artifact inventory could not be completed.
- The Android WSI/gralloc/acquire/present compatibility matrix remains
  incomplete.
- The proposed sparse design remains unimplemented/unverified in the evidence
  reviewed.

## Audit disposition

**PARTIAL / NOT APPROVED.** Documentation corrections resolved the bounded
issues above, but B5 remains blocked and B1-B4 remain partial pending the
missing phase artifacts, deeper source traceability, and separately
authorized validation. The plan's approval criteria have not been met.
