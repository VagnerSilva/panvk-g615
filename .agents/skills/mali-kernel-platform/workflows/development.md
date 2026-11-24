# Workflow — correction, feature, refactor and optimization

## When and prerequisites

Default for a development task with a known domain. Read
[implementation recipes](../references/implementation.md) and
[decisions](../references/decisions.md), then use existing discovery only to
confirm necessary inputs. Do not start with a new general investigation.
This skill's construction does not authorize real Mesa implementation.
Future implementation must follow AGENTS and the separately approved scope.

## Sources and steps

1. Classify the task: defect, feature, behavior-preserving refactor or
   optimization. State requested behavior/output and one measurable acceptance
   condition. Select the mapped function, source target and dependent callers.
   A known bug uses its recipe immediately; collect only a prerequisite that
   is actually missing. Do not use a firmware hypothesis to replace source facts.
2. For Mesa changes, compare selected post-series source with the input locator. Keep
   pin, profile, default/opt-in variant, original changes and source identity.
   If the behavior already exists, stop with a no-op result and evidence.
   Missing exact post-series source blocks a real edit; a labeled demonstration
   may use the exact overlay base without claiming final-tree applicability.
3. Choose the smallest correction using the mapped contracts:
   - Defect: isolate the violated invariant and an edge case that fails before
     the fix; repair ownership/error and directly dependent callers together.
   - Feature: reuse the existing interface; define success, unsupported/error
     and observable output. New exposed contracts require explicit approval.
     Stage host logic, integration and runtime separately.
   - Refactor: preserve signatures, lock order, requests/states/errors and
     default policy; compare identical before/after cases against observed
     baseline behavior, not an aspirational error contract. Keep preexisting
     error changes out of a behavior-preserving refactor.
   - Optimization: first prove semantic equivalence; keep a baseline and
     controlled comparative method. Without measurements, claim only a proposal.
4. Choose the editing flow by target, preserving paths, modes and user changes:
   - Mesa driver changes targeting `work/mesa/`: use a separate approved
     disposable copy, stage the baseline without committing and generate a
     patch with `git diff --binary --full-index`. Keep it in its proper family;
     follow [metadata](../../../../patches/README.md:3), dependency order and
     provenance. Do not edit protected originals or silently replace approved
     patches/profiles/lock.
   - Other project files, including skills, documentation, scripts, tests and
     apps: edit directly within the requested scope. Review the diff; no
     generated patch, patch check or patch application step is required.
5. Validate the exact requirement in this order:
   - Source/contract/ABI checks and small host/mock regression cases for changed
     branches; before must fail where a defect is fixed, after must pass.
   - Affected target/caller compilation in each claimed ABI, using the
     [build specialist](../../panvk-build-validation/SKILL.md). For documentation
     or illustrative patches, compilation can remain NOT EXECUTED.
   - For Mesa patches only, exact check:
     `rtk git apply --check --whitespace=error -v <patch>`.
     Reject conflict/offset/fuzz. This check never applies a patch.
   - For Mesa changes, only after separate approval, strict reconstruction/build and the
     smallest bounded [device gate](device-validation.md). Device PASS does not
     replace host error-path tests or prove stability/performance.
6. Inspect the complete diff and directly dependent behavior, plus the
   prepared patch when changing Mesa.
   Report the initial failing stage/error and delivered error separately,
   tests/commands/actual outputs, intended effects,
   unexecuted gates, risks and any explicitly deferred decision.

## Domain acceptance and failure

Use each recipe's focused cases, not an unrelated full CTS/build as a proxy.
For a source defect, test success and partial failures for the changed ownership
or state; add only missing tests directly covering the change. No unavailable
fixture is described as already implemented. Create a small isolated mock
fixture only when required and approved; label model-only evidence separately
from compiled source and runtime.

Stop on source/contract mismatch, missing required authorization, unsafe
cleanup or a violated invariant. Do not broaden into kernel internals, restore
JM or retry device failures to rescue a patch. Unknown internal behavior can
block that feature while leaving unrelated mapped work executable.

## Evidence, delivery and authorization

Deliver function/file map, preserved contract, concrete edit design,
reviewable diff (Mesa patch/base/metadata only when applicable), focused outcomes and dependent
risks. Use [evidence classes and gates](../references/validation.md).
Distinguish demonstration/model/source/build/device evidence explicitly.

No application, commit, profile/contract replacement, installer, hardware
test, firmware/policy change or optimization promotion is authorized here.
Final approval and application remain separate from operational exercises.
