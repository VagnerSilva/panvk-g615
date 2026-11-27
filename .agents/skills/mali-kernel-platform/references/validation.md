# Evidence, gates and delivery contract

## Evidence classes

| Class | Meaning |
|---|---|
| STATIC_CONFIRMED | Exact source/header/input/document content inspected |
| REPRODUCED | Behavior reproduced by an identified experiment |
| BUILD_VALIDATED | Identified target build completed |
| AUTOMATED_TEST_VALIDATED | Identified automated test executed with recorded result |
| DEVICE_VALIDATED | Relevant test executed on Moto with matching artifact/context evidence |
| HISTORICAL_REPORT | Earlier reported result; not reproduced or independently verified in this investigation |
| INFERRED | Interpretation supported by indirect evidence; state assumptions |
| HYPOTHESIS | Falsifiable explanation not yet confirmed |
| UNKNOWN | Missing or non-verifiable fact |

Document existence is static; the execution it describes can still be
historical. Never relabel old results because their file survives a reset.
Keep [E-001–E-021](../../../../docs/engineering/mali-kernel-platform/EVIDENCE_REGISTER.md)
and [historical audit](../../../../docs/engineering/mali-kernel-platform/audit/CONSOLIDATION_AUDIT.md)
intact. Independent audit of this skill is a separate gate.

## Evidence record and required output

For each claim record: ID/claim, class, exact file/symbol/line or patch locator,
Mesa/source snapshot and selection/variant, ICD SHA-256/Build ID/manifest,
device/GPU/PAN_ARCH, libc/platform, process context, UAPI/page/kernel/firmware
when known, date, command/procedure, expected/actual result and limitations.
Use UNKNOWN for missing fields; never substitute MC6 or privileged-control data.
Minimize identifying process/device data not needed for the technical claim.

Deliver:

1. Problem, scope and first causal gate.
2. Input/binary/context identities and precise evidence locators.
3. Facts, observations, hypotheses and unknowns separately.
4. Proposed action/patch, authorization boundary and affected paths.
5. Gate table with commands and actual results, risks and next bounded step.

## Gate statuses and scope

Use `PASS`, `FAIL`, `BLOCKED`, `NOT EXECUTED` separately for provenance,
source/ABI, build, package/static binary, functional execution, stability,
performance and skill audit. UNKNOWN is an evidence class, not a passing gate.
Missing mandatory prerequisites mean BLOCKED; absent voluntary execution means
NOT EXECUTED. A static discrepancy can be FAIL static without a runtime FAIL.

Assertions measure ABI layout, not vendor handler compatibility. Enumeration
is not execution; pending/signal FD checks are not cache/readback; offscreen is
not presentation; a bounded successful run is not endurance or recovery.
Do not claim performance without a controlled comparative measurement.

## Verification and patch boundary

Use verified [repository tests](../../../../tests/README.md), selecting only
the relevant bounded case. Reuse existing matching logs before new runs.
For documentation verify frontmatter, structure, links/anchors/locators and
traceability; independent operational audit follows generation.

Prepare source/doc patches in an isolated copy with exact baseline and
`git diff --binary --full-index`. Run
`rtk git apply --check --whitespace=error -v <patch>` without applying.
Reject conflicts, offsets/fuzz; do not recount/force a patch to appear valid.
Application, builds touching sources and hardware tests need explicit approval
and the disposable workflow in AGENTS. Never mutate protected originals.
