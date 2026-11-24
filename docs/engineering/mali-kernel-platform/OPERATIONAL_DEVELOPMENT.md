# Operational development revision

Date: 2026-11-23. The second user plan groups consolidation, construction,
operational exercises and final approval instead of reopening seven phases.
Existing sources, decisions, findings, audits and deferred limits are preserved.
No Mesa source implementation, hardware run or patch application is part of
building this skill.

## Input reuse and actual gap

The [technical consolidation](TECHNICAL_CONSOLIDATION.md) already supplies
the contracts and known defects. The prior skill primarily guided diagnosis.
The new work adds the missing conversion to nominal edit sites, dependent
functions, concrete correction/feature/refactor/optimization steps and focused
validation. Only symbol/call-site lookups were needed; no general kernel,
F0–F5, AHB or build reinvestigation was opened.

## Proposed operational entry

- [Skill](../../../.agents/skills/mali-kernel-platform/SKILL.md).
- [Development map/recipes](../../../.agents/skills/mali-kernel-platform/references/implementation.md):
  UAPI, CSF, memory/VA, DMA-BUF/cache, sync_file/KCPU, initialization/firmware,
  Android, glibc, Mesa/Kraid and inactive JM boundary.
- [Decision matrix](../../../.agents/skills/mali-kernel-platform/references/decisions.md):
  approved decisions, contracts, limits, rejected shortcuts and blocking gaps.
- [Development workflow](../../../.agents/skills/mali-kernel-platform/workflows/development.md):
  defect, feature, behavior-preserving refactor and measured optimization.

The operational skill has 19 files: entry point, twelve references and six
workflows. Diagnostic routes remain available only for concrete missing facts;
they are not the default instruction to rediscover the subsystem.
An unavailable applied snapshot blocks real source application, not an
explicitly labeled demonstration using an identified overlay base.

## Patch-scope correction

The user clarified that mandatory patches apply only to driver changes
targeting `work/mesa/`, prepared in a separate copy. Skills, documentation,
scripts, tests and apps use direct edits with diff review, not generated
delivery patches. The earlier documentary cumulative patch is superseded
as a delivery mechanism; it remains historical, not an installation input.
The development workflow and platform-observation recipe now distinguish
these paths. Historical audit reports and illustrative patches are preserved
unchanged; the non-Mesa probe patch is not a template for future delivery.

## Operational acceptance

An independent reviewer must exercise five development tasks: DMA-BUF import,
sync-file flow, CSF management, ABI compatibility and platform capability.
For each, require the component/function map, edit design, preserved contract,
reviewable demonstration patch/base, focused checks and dependent risks.
No exercise modifies/applies real Mesa. Models, patch checks, compiled source
and device execution must be separately labeled.

The prior ten diagnostic walkthroughs and their timeout/reference corrections
are preserved, not rerun as a new full audit. The operational review is the
single audit of this changed development objective; defects trigger only the
affected exercises/checks, not another general investigation.

## Approval boundary

The earlier limited operational contract was explicitly accepted. The user
authorized direct installation of this development extension under Plan 2
on 2026-11-23. This does not
replace the earlier independent report with an invented APPROVED disposition.
Mesa patch application, app/driver installation, profile/contract changes,
commits and hardware tests still require separate authorization. Existing runtime limits
do not disappear because development exercises succeed.

## Operational audit result

The single independent operational auditor executed five exercises:
DMA-BUF import correction, sync-file wait correction, CSF page-layout
refactor, ABI selector no-op with evidence, and CPU-page-size observation.
Four illustrative patches and one justified no-op were produced against
identified overlays/snippets; none claims applicability to final Mesa.

The initial report remains PARTIAL and unchanged. Its two specific findings
were corrected:

- D1: separate initial CSF failure from errno delivered after failing TERM;
  classify replacement as a preexisting limitation, not a refactor guarantee.
- D2: require retry after an INT_MAX-clamped poll chunk until the actual
  deadline, and explicit two-poll/sub-ms unsignaled acceptance cases.

Only E2/E3 were repeated by the same auditor. The separate closure records
APPROVED DOCUMENTAL/OPERACIONAL for the demonstrative scope, with no concrete
remaining instruction defect. The review bundle retains the initial report,
closure, identified fixtures, illustrative patches, commands and results.
No historical independent disposition was retroactively changed.

| Gate | Evidence and scope |
|---|---|
| Five operational exercises | PASS MOCK; E1/E2 reproduce 17/8 baseline violations and zero candidate violations |
| Focused D1/D2 closure | PASS; E2 deadline assertions and E3 baseline-equivalent error/request traces |
| Demonstration patch checks | PASS against named overlay/snippet/probe bases; no application |
| Real selected Mesa replay/application | NOT EXECUTED |
| Bionic/glibc driver and caller builds | NOT EXECUTED |
| Device, coherency, concurrency, real 16KiB and stability | NOT EXECUTED |
| Comparative performance | NOT EXECUTED |
| Skill installation under Plan 2 | Authorized by the user on 2026-11-23; direct file installation, no documentary patch |
| Mesa patch application, hardware tests and publication | Not authorized by this audit or skill installation |

The operational acceptance question is satisfied for these bounded source/
demonstration tasks: the agent selected edit sites, contracts and checks
without reopening the existing investigations. It is not proof that every
kernel, runtime or firmware task can proceed without additional evidence.
