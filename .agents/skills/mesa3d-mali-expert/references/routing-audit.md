# Routing audit and homologation

Delivery 4: audit and homologation of the inventory, matrix and
[revised central skill](../SKILL.md). Date: 2026-11-24.

## Method and limits

Documentary exercises using requests without files, symbols or skill names.
Rubric: select the owner by objective/stage, justify boundaries, declare
conditional dependencies and order, avoid unnecessary activations, and
do not presume a cause, support or authorization.

The results below are the executor's documentary evaluation using central and
the [matrix](responsibility-matrix.md), not execution of a routing engine,
driver testing or hardware homologation. Automated link checks also do not
prove semantic decisions. Final approval belongs to the user.

## Controlled exercises

| ID | Request without internal structure | Evaluated route / justification | Dependencies and limits | Documentary result |
|---|---|---|---|---|
| R01 | Correct a panic in NIR shader translation in the Kraid backend | Compiler: internal translation already identified by the error | Build after Mesa fix; GPU only if hardware acceptance requires it | PASS |
| R02 | Implement Vulkan descriptor functionality | PanVK: API contract/state consumed by the driver | Compiler only if translation is affected; build and GPU according to acceptance | PASS |
| R03 | Correct ioctl structure size during CSF queue creation | Platform: UAPI/layout | PanVK only if the caller contract changes; focused build and GPU afterward | PASS |
| R04 | Resolve an Android link error caused by a host library in a cross-build | Build: host/target separation, not shader translation | Do not start compiler/kernel/GPU as presumed causes | PASS |
| R05 | Compare timings of two ICDs with valid identity and build handoffs on the Moto | GPU: comparative evaluation | No rebuild; confirm authorization/context/metrics before hardware | PASS |
| R06 | Add a Vulkan feature requiring new backend NIR translation | PanVK defines contract, compiler implements translation, PanVK integrates | Build candidate; functional GPU when required/authorized; platform is not automatic | PASS |
| R07 | Coordinate global Kraid integration while preserving Mesa consumers | Central: shared architecture/interfaces | Compiler/PanVK only for affected contracts; no nonexistent migration skill | PASS |
| R08 | The shader does not compile; no error or stage is available yet | Central keeps cause unknown and requests error/operation | Provisional selection is not a cause; no paths required or blanket loading | PASS |
| R09 | rustc cannot find a dependency during the driver build | Build: toolchain/dependency | Do not confuse rustc with Kraid shader translation | PASS |
| R10 | A Vulkan barrier does not make writes visible to the next dispatch | PanVK: dependency/visibility contract | Platform only if evidence reaches cache/kernel protocol; GPU reproduction as needed | PASS |
| R11 | A sync_file waiter leaks FDs after signaling | Platform: lifetime/fence/FD | PanVK only for an affected consumer, not as waiter owner | PASS |
| R12 | Measure whether a workload is memory-bandwidth-bound | GPU: profiling and discriminating hypothesis | Do not invent unavailable counters or attribute cause to the allocator | PASS |
| R13 | Vulkan became slow without measurements or a known cause | GPU: measure before choosing a fix | Compiler/PanVK/platform only after evidence | PASS |
| R14 | The ICD cannot load because an ELF dependency is missing | Build: loader/dependencies | Do not start WSI/GPU corrections; diagnosis does not authorize installation | PASS |
| R15 | Run a JM/Panthor benchmark on another GPU | Central: request outside the frozen target | Declare gap/scope decision; do not infer homologation from historical boundaries | PASS |
| R16 | The indicated specialized skill is not installed | Central: verify availability and declare gap | Verified guidance or decision; no fictitious invocation or success-shaped fallback | PASS |
| R17 | Implement the complete Gallium driver | Central: gap beyond relevant Panfrost interfaces | Bound scope and obtain a decision; do not treat PanVK as a general Gallium specialist | PASS |
| R18 | A rule requires an action incompatible with an approved contract | Central: state conflict and obtain a decision | Stop only the affected action; no invented technical precedence | PASS |

R01-R07 cover the seven original required scenarios. R08-R18 cover
ambiguities, exclusions, availability and authorization.

## Separate-context exercise and review

The `routing-audit` agent received the 18 requests without implementation
locators and read only central before formulating decisions. It then compared
the three documents and reviewed the complete diff and additions.
No specialist was activated to execute tasks, and no hardware was accessed.

Result: **17 concordant decisions and R15 partially concordant**.
For R15, the agent placed GPU as a blocked candidate, with central deciding
scope before execution; the rubric requires central to be primary immediately.
No improper authorization occurred. The documentary verdict was favorable,
without a material defect in boundaries, references, loops or permissions.

Executor correction: make the scope gate explicitly precede execution
ownership in central and the matrix. R15 therefore stays with central,
regardless of the word "benchmark". The executor reviewed the correction;
**it received no new independent audit**. The original partial result is
preserved, not converted to independent 18/18.

## Corrections and preservation

- Replaced the missing `mesa-kraid-migration` route with central coordination
  of existing specialists.
- Concrete links to all five specialists; classification by objective and
  stage before locating code.
- Explicit boundaries for compilation, memory, sync, ICD and optimization.
- Conditional sequences, availability, loop prevention and a single handoff.
- Global Kraid architecture preserved without expanding operational scope.
- MC6 profile, glibc opt-in and historical evidence not promoted to Moto PASS.
- Technical procedures kept in specialists; global rules unchanged.

## Gates and approval

| Gate | Status | Evidence / limit |
|---|---|---|
| Inventory and matrix | PASS | Six technical entries and five process entries inspected; gaps recorded |
| Executor exercises | PASS | 18 documentary decisions in the table, including the seven required cases |
| Original structure, links and whitespace | PASS | Offline validator: six frontmatters, four documents, 42 valid links, five routes and 18 records; `git diff --check` exit 0 before translation/cleanup |
| Original complete diff review | PASS | Executor and agent examined central and three additions; subsequent scope correction reviewed by executor |
| Full separate-context concordance | BLOCKED | 17 concordant and R15 partial; subsequent correction without independent reaudit; user accepted the limitation, not an independent 18/18 result |
| ICD build/ELF/package | NOT EXECUTED | Outside the documentary change |
| Hardware/stability/performance | NOT EXECUTED | No device accessed, workload executed or result extrapolated |
| Final documentary homologation | PASS | User explicitly approved the deliveries, R15 correction and limitations on 2026-11-24 |

Original verification commands: `python3 validate_skill_integration.py`,
using the session's temporary validator (not production tooling), and
`git diff --check`. The first directly checks whitespace in untracked
additions, which the tracked diff alone does not cover. Original structural output:
`PASS: 6 skill frontmatters, 4 documents, 42 resolved file links,
whitespace/newlines, 5 concrete routes, 18 scenario records`.
These checks do not evaluate semantic decisions or GPU behavior.

## User acceptance

On 2026-11-24, after receiving all four delivery links and the results
(17 concordant, R15 partial, correction without a new independent audit),
the user selected **approve**, explicitly including the R15 correction and
recorded limitations. Homologation is documentary with that accepted limit;
it does not authorize Mesa changes, wider support, hardware execution,
commits or publication. The original independent audit remains partial
for R15 despite documentary acceptance.

The global/specialist divergences identified in the
[inventory](inventory.md) remain recorded without contract/profile changes.
The router does not silently resolve real conflicts. All four deliveries were
accepted; hardware validation remains outside this delivery.

## English-only cleanup

The user subsequently requested English skill content and removal of obsolete
planning files and references. This translation preserves the original audit,
acceptance and limitations; it is not a new independent routing review.
Technical scope, procedures and command blocks remain unchanged.

Cleanup verification: the temporary session checker
`python3 check_skill_cleanup.py` scanned 47 Markdown documents, confirmed
no remaining obsolete planning files/references or Portuguese markers,
and compared all surviving fenced blocks against their pre-translation
contents. Changed-document links and whitespace passed; `git diff --check`
returned exit 0. Language was reviewed manually; marker checks alone do not
establish English prose.

Two unrelated pre-existing issues were reported and left unchanged:
a missing reviewer-template link in
[executing-plans](../../executing-plans/SKILL.md), and a newline/whitespace
issue in [kraid-compiler](../../kraid-compiler/SKILL.md).
All 11 obsolete planning files under skills were removed after their
references. Historical records outside skills, global rules, source inputs
and profiles were preserved. No build, hardware run or new independent
routing audit was performed.
