---
name: kraid-compiler
description: "Use when investigating, implementing, reviewing, or validating Mesa Kraid compiler work: NIR translation and lowering, Kraid IR, legalisation, optimizations, scheduling, liveness, register allocation, spilling, ISA, code generation, or compiler tests."
---

# Kraid Compiler Engineering

## When to use

Use this skill for compiler-local work on Kraid: NIR translation, Kraid IR,
legalization, optimization, scheduling, liveness, register allocation,
spilling, ISA encoding/decoding, code generation, diagnostics, and compiler
tests. Use the central [Mesa and Mali skill](../mesa3d-mali-expert/SKILL.md)
for cross-subsystem routing. Hand off Panfrost/PanVK, kernel/UAPI, build, or
hardware-performance questions to their relevant specializations when those
domains are primary.

## Authority and source boundaries

- Follow the repository `AGENTS.md` and the central skill for approval,
  patch-only workflow, source-tree protection, and validation reporting.
- Treat `work/mesa/` as read-only. Make Mesa source changes only through the
  repository's patch workflow, against the pinned source in `sources.lock`.
- Before investigating, record the Mesa commit, profile/configuration, Git
  status, and any local source changes. Do not treat modified files as clean
  upstream evidence or overwrite pre-existing work.
- For each revision-dependent technical claim, record the exact Mesa commit,
  source file and symbol, relevant build/runtime conditions, and test or
  supporting evidence when applicable. Distinguish:
  - **Revision-bound:** confirmed only for the examined revision.
  - **Cross-revision verified:** confirmed in multiple named revisions.
  - **Unknown:** not confirmed for the current revision.
- Separate confirmed facts, observations, hypotheses, and unknowns. Do not
  treat an old observation as current, use documentation alone to prove code
  behavior, or generalize across architectures. Revalidate claims when source
  or configuration changes; this skill's examples are not a substitute for
  current source inspection.

## 1. Reconstruct the compiler pipeline

Start with `src/panfrost/compiler/kraid/compile.rs`, `lib.rs`, `meson.build`,
`kraid.h`, and the Mesa compiler call sites. Trace the executed call order,
conditional passes, inputs/outputs, and validation boundaries. At the audited
source revision, the main sequence is:

1. Translate NIR into Kraid IR and run the initial pass boundary.
2. Rematerialize constants, widen ALU operations, and legalize source swizzles.
3. Iterate copy propagation, destination-modifier propagation, and fusion
   until the loop reports no progress.
4. Lower vector/swizzle forms; optimize variables and DCE; normalize and lower
   constants; promote immediates only when the FAU input enables it.
5. Optimize execution units, schedule for register pressure, and legalize.
6. Assign registers. This step may spill, repair SSA, run DCE, and allocate
   spill storage before final register allocation.
7. Lower copies, then thread jumps and simplify fall-through. These CFG passes
   occur after register allocation because they can add critical edges.
8. Assign message slots, insert required waits, mark reconvergence, and
   optimize flow. Respect the source comments that constrain removal or
   movement of instructions after these final scheduling/flow passes.
9. Lower blend calls as required and encode for the selected model.

Re-derive this order for every source revision. Do not move a pass based only
on its name; establish its preconditions, postconditions, and downstream
consumers first.

## 2. Build an evidence-based NIR support matrix

Trace `nir.rs` together with the compiler options and preprocessing/lowering
that produce its input. Record entries per operation, bit size, stage, and
architecture where relevant; classify each as **direct**, **after lowering**,
**partial**, **unsupported**, or **not verified**.

For each investigated operation, record:

| Operation | Type | Stage | Architecture | Support | Condition | Evidence | Test |
|---|---|---|---|---|---|---|---|
| NIR op/intrinsic/texture | Bit size and format | Applicable stage | Model/generation | Direct, after lowering, partial, unsupported, or not verified | Lowering, precondition, or limitation | File, symbol, revision | Test name or gap |

The translator has explicit paths for constants, ALU, texture operations,
intrinsics, and phi instructions. Jump instructions participate in CFG
construction; other instruction kinds reach an unsupported fallback. ALU,
texture, and intrinsic matches also contain unsupported fallbacks. Therefore:

- A match arm proves only that specific translation path exists; it does not
  prove all NIR operations, types, stages, or architectures in that family work.
- Verify the applicable `nir_shader_compiler_options`, earlier Mesa lowering,
  architecture conditions, and any operation-specific assertions.
- Preserve the exact unsupported operation and triggering shader when
  diagnosing a translation failure. Do not silently classify a panic/fallback
  as a valid lowering path.
- Include a regression test for each newly supported or changed translation
  path, and distinguish compiler-unit coverage from hardware execution.

## 3. Preserve Kraid IR invariants

Read `ir.rs`, `ops.rs`, `data_type.rs`, `model.rs`, `ssa_value.rs`, `phi.rs`,
`flow.rs`, `swizzle.rs`, and `validate.rs` as a connected representation.
Trace definitions and uses, SSA widths, phi construction, block/CFG edits,
source and destination typing, swizzles, memory effects, hidden state, and
special registers through every changed operation.

When changing an invariant, identify its representation, producers,
consumers, validation, required repair/recomputation, and risk. Distinguish
properties enforced by data structures from those maintained by convention:

| Invariant | Representation | Producers | Consumers | Validation/test | Repair or recomputation | Risk |
|---|---|---|---|---|---|---|
| Property to preserve | Structure/symbol | Creating or changing passes | Dependent passes | Actual check | SSA, liveness, or metadata work | Failure if violated |

Use `Shader::validate` and relevant focused tests after transformations. Check
what the validator actually enforces in the current revision; a successful
validation call does not imply every CFG, ISA, or semantic property is checked.
When a pass changes SSA or CFG, identify which consumers require repaired SSA,
recomputed liveness, or rebuilt metadata.

## 4. Audit legalization and optimization passes

For each pass in `compile.rs`, `legalize*.rs`, `lower_*.rs`, `small_constants.rs`,
`widen_alu_ops.rs`, `remat_constants.rs`, `opt_*.rs`, `jump_thread.rs`,
`reconvergence.rs`, and `repair_ssa.rs`, record:

- The actual call site and any gating condition.
- Preconditions and resulting representation/invariants.
- Whether it changes instructions, types, SSA, CFG, memory effects, or flow.
- Architecture/model constraints and the consumers that depend on its output.
- A focused regression test and any broader validation needed.

| Pass | File/call site | Condition | Preconditions | Transformations | Postconditions | Dependencies/consumers | Tests |
|---|---|---|---|---|---|---|---|
| Symbol | Location and order | When it runs | Required input state | Instructions, types, SSA, CFG, memory, or flow | Produced state/invariants | Required earlier/later passes | Existing coverage and regression needed |

Construct ordering dependencies from the implementation and call sites rather
than from filenames. Re-check validation before/after passes and use narrow
tests to isolate semantic regressions.

## 5. Trace scheduling, liveness, allocation, and spilling together

Follow `schedule.rs`, `required_waits.rs`, `message_slots.rs`,
`reconvergence.rs`, `liveness.rs`, `ra.rs`, `spill.rs`, `parallel_copy.rs`, and
`repair_ssa.rs` as one pipeline. Verify SSA dependencies plus memory, barrier,
hidden-register, discard, message-slot, and flow hazards before changing
instruction order. Confirm whether a dependency is encoded in the scheduler,
wait insertion, or another pass; do not infer it from SSA alone.

For each affected dependency or allocation constraint, trace its origin, the
component that enforces it, the passes that produce or consume it, and the
relevant state before and after the transformation:

| Dependency or constraint | Origin | Protection mechanism | Passes involved | State before/after | Test/evidence |
|---|---|---|---|---|---|
| Hazard or allocation constraint | SSA, memory, barrier, or special state | Scheduler, waits, allocator, or other verified mechanism | Producers and consumers | Property that must be preserved | Focused test or source evidence |

Do not assume every dependency is represented by SSA. Distinguish ordering
dependencies from allocation constraints, identify how transformations affect
liveness, and note when SSA or derived metadata must be rebuilt. Do not claim a
reordering is safe without evidence for each relevant dependency.

For allocation changes, trace live-in/live-out and pressure recomputation,
register constraints, spill candidates, generated loads/stores, SSA repair,
spill-slot allocation, and re-allocation. The current implementation has a
specific no-spill assertion for blend shaders; verify whether the shader path
under investigation is subject to it. Do not use register count or spill count
alone as proof of performance improvement.

## 6. Keep ISA claims generation-specific

Trace `model.rs`, `isa.rs`, `encode_v9.rs`, `decode.rs`, `proc/isa/`, the ISA
XML inputs, and the generator/disassembler tools. Build a generation matrix
from the model dispatch, generated encoder/decoder ranges, instruction
availability checks, and tests. The presence of an XML file or generated
symbol alone is not proof that `model_for_arch` accepts that architecture or
that the full compiler path supports it.

At the audited revision, `model_for_arch` accepts Valhall architectures 9–14
and rejects architecture 15 and later; generated encode/decode ranges also
cover 9–14. Re-check the code before reusing this statement. Do not conflate
different ISA generations or transfer Bifrost assumptions to Kraid.

Record compatibility by generation and keep model dispatch, encoder, and
decoder evidence separate:

| Architecture | Model accepted | Encoder range | Decoder range | Instruction constraints | Full codegen path | Tests | Status |
|---|---|---|---|---|---|---|---|
| Generation/model | `model_for_arch` evidence | Verified range | Verified range | Availability/restrictions | End-to-end evidence | Coverage or gap | Confirmed, partial, or not verified |

## 7. Validate compiler and hardware behavior separately

- Inspect the current Meson configuration and `src/panfrost/compiler/kraid/meson.build`
  before choosing tests. The Rust test target is conditional; hardware tests
  are skipped by default in its configured invocation.
- Run focused software/unit tests first, then the narrowest applicable broader
  compiler suite. Report build/test gates as `PASS`, `FAIL`, `BLOCKED`, or
  `NOT EXECUTED` and include the exact revision and command.
- Hardware tests require a compatible, authorized device. Inspect the runner
  and submission/wait behavior first; do not assume an internal timeout. Bound
  hardware runs externally, use small workloads, and stop on unsafe or
  unresponsive behavior.
- Keep functional correctness, stability, register pressure/spilling,
  compilation time, and performance as separate outcomes. Performance claims
  require a controlled baseline and repeated comparable measurements.

For each executed validation, preserve enough information to reproduce and
scope the result:

| Category | Record |
|---|---|
| Code | Exact Mesa commit, worktree status/local changes, `sources.lock` and profile |
| Host | Operating system and host architecture |
| Toolchain | Rust, C/C++ compiler, and other relevant tool versions |
| Build | Meson version/options, build configuration/directory, and target |
| GPU | Vendor, model, and GPU architecture |
| Kernel | Version and relevant configuration |
| Firmware | Identifiable version, or explicitly unavailable/not applicable |
| Runner | Type, configuration, and execution conditions |
| Tests | Exact build/test commands, results, and relevant logs |
| Limitations | Environmental constraints and any unavailable/not-applicable fields |

Record unavailable information explicitly; do not imply an inapplicable field
is a confirmed value. Preserve original commands and outcomes. Label unit,
integration, build, hardware, CTS, stability, and benchmark/profile results
separately. Do not assume two builds are equivalent because they share a
commit, compare benchmarks without checking environmental equivalence, or
confuse environmental limitations with compiler failures. Never report an
unexecuted check as passed or infer runtime correctness from a successful build
or unit test.

## Investigation handoff

Report the source commit and worktree caveats; affected operations, files, and
symbols; the NIR/ISA support classifications; relevant pass ordering and
invariants; observed evidence versus hypotheses; focused tests and outcomes;
and remaining unknowns. For a proposed change, state its semantic risk,
downstream consumers, regression test, and unexecuted validation gates.