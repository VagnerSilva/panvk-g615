---
name: panfrost-panvk
description: "Use when investigating, implementing, reviewing, or validating Mesa PanVK Vulkan behavior on Arm Mali: device initialization, features, graphics and compute pipelines, descriptors, resources, memory, synchronization, submission, WSI, or Panfrost integration. Route compiler internals, kernel/UAPI, build, and hardware-testing work to their verified specialist skills."
---

# PanVK and Panfrost Engineering

## Purpose and scope

Use this skill for the Vulkan driver in Mesa's PanVK and for the Panfrost
components needed to understand its integration. PanVK is the primary domain;
Panfrost is a reference for shared infrastructure and interfaces, not a reason
to expand an investigation into the complete Gallium driver.

Trace behavior from the Vulkan contract through the actual PanVK implementation
and, when relevant, to command generation, kernel interfaces, and hardware.
Treat the Mali-G615 MC6, Pan architecture 11, and CSF as the project's initial
reference configuration, not as the limit of supported hardware.

This skill guides investigation and code changes; it does not authorize edits
to protected source trees, patch application, commits, or publication. Follow
the repository `AGENTS.md` and the central
[Mesa and Mali skill](../mesa3d-mali-expert/SKILL.md) for authority,
provenance, patch workflow, and validation reporting.

## Responsibilities and routing

Keep the primary fault domain explicit and hand off only the part that belongs
to another specialization:

| Work | Responsibility |
|---|---|
| Vulkan API entry points, feature exposure, PanVK objects, pipelines, descriptors, resources, synchronization, submission, and WSI | This skill |
| Panfrost shared libraries, GPU descriptions, GenXML, command helpers, or Gallium differences needed to explain PanVK | This skill, limited to the relevant interface |
| NIR translation internals, Kraid IR, lowering, optimization, scheduling, liveness, allocation, spilling, ISA, and code generation | [Kraid compiler skill](../kraid-compiler/SKILL.md) |
| Android/Bionic or glibc build, packaging, ICD, and build gates | [PanVK build-validation skill](../panvk-build-validation/SKILL.md) |
| Kbase/UAPI, CSF/JM kernel protocol, firmware, or kernel memory behavior | [Mali kernel/platform skill](../mali-kernel-platform/SKILL.md), after checking availability and its Moto G86/G615 MC2, Android/glibc scope; other backends/devices are boundaries, not qualified targets |
| CTS, device test execution, stability, profiling, or benchmarks | Use a matching testing skill only after confirming it is present and inspecting it |
| Cross-cutting Mesa migration, shared compiler architecture, or upstream divergence | Use the central skill and verify whether a dedicated migration skill exists |

The central skill may list specializations that are not installed in the
current workspace. Do not invent their contents or assume they can be loaded:
check for the skill first. If it is unavailable, state the boundary and follow
the repository's documented workflow without claiming specialist procedures.

Before routing to any specialization, verify that its `SKILL.md` exists in the
active workspace and read its current instructions. A link in this document or
the central routing table is not proof that the target skill is installed.
Keep the handoff within that skill's stated scope; if it is unavailable, retain
the investigation locally using verified guidance and explicitly state the
missing specialization.

For cross-domain issues, identify the PanVK boundary and pass a concise handoff:
reproduction conditions, exact source revision and configuration, relevant
paths/symbols/interfaces, evidence, hypotheses tested, validation, and open
questions. Do not silently transfer ownership of the entire investigation.

## Authority, provenance, and source boundaries

Before analyzing behavior or changing code:

1. Read the applicable `AGENTS.md` and inspect repository status. Preserve
   existing changes; do not assume a clean worktree.
2. Record the Mesa commit from `sources.lock`, the selected profile, patch
   series identifier when relevant, and the actual source-tree commit/status.
   The extracted `work/mesa/` tree may contain applied patches or local edits;
   distinguish those from the pinned upstream commit.
3. Treat `work/mesa/` and other protected source trees as read-only. Make Mesa
   changes only through the repository's authorized patch workflow and the
   correct patch family. Do not apply a patch or commit without explicit
   authorization. Files outside Mesa, including skills, documentation,
   scripts, tests and apps, use direct edits rather than generated patches.
4. Confirm paths, symbols, generated files, build options, and test targets in
   the source revision under investigation. Candidate roots such as
   `src/panfrost/vulkan/`, `src/panfrost/lib/`,
   `src/panfrost/lib/genxml/`, `src/gallium/drivers/panfrost/`,
   `src/compiler/nir/`, and `src/panfrost/compiler/` are not guaranteed to
   exist or have the same contents in every revision.
5. Prefer the checked-out implementation and matching interfaces over generic
   documentation. Use other repositories or historical branches as leads,
   never as proof of current behavior.

For every conclusion, label its evidence as one of:

- **Confirmed** — established by the applicable source/specification or
  reproducible evidence, with revision and conditions.
- **Observed** — behavior was seen, but its cause or generality is unknown.
- **Hypothesis** — a falsifiable explanation not yet verified.
- **Unknown** — not established by available evidence.

Scope revision-bound claims to the source commit, local modifications, GPU
model/architecture, frontend, kernel/UAPI, firmware, platform, configuration,
and workload as applicable. A code path in a modified worktree is not clean
upstream evidence. A reported Vulkan feature is not proof that its execution
path is correct.

## Reconstruct the PanVK architecture

Build the architecture map from the current revision rather than assuming a
fixed file layout. Find and follow the implementations for:

- Instance creation, physical-device discovery, GPU identification, and
  architecture/version dispatch.
- Physical-device properties, extensions, feature reporting, and device
  creation/initialization and failure cleanup.
- Queues, queue families, command pools, command buffers, and object lifetime.
- Shared Vulkan runtime helpers, Panfrost libraries, the active backend, and
  the kernel interface, when used by the target configuration.

For each transition, record the caller and callee, inputs and outputs, relevant
conditions, error behavior, and ownership of the state. Identify which
behavior is shared and which is version-, architecture-, frontend-, backend-,
or platform-specific. Do not infer support from a filename, a declaration, an
extension table, or one architecture's implementation.

## Trace Vulkan functionality end to end

For a feature or API operation, trace:

1. The Vulkan entry point, structure, and required API/extension contract.
2. Feature/extension reporting and any enablement or device-creation checks.
3. The implementation path: state changes, validation, command recording,
   generated work, and error paths.
4. Dependencies on shader compilation, resources, synchronization, and
   architecture-specific hardware behavior.
5. The kernel/backend mechanism, only when the path actually reaches it.
6. Tests that cover the exact operation, conditions, and target generation.

Treat the evidence sources as distinct:

| Source | Establishes | Does not establish by itself |
|---|---|---|
| Vulkan specification | Required API contract for the applicable version/extensions | That PanVK implements or satisfies the requirement |
| PanVK/Mesa source | The code path and conditions present in the inspected revision | Successful execution or correctness on hardware |
| Tests | Behavior exercised by the named test and configuration | Complete feature coverage or behavior outside that test's scope |
| Hardware run | Observed behavior on the recorded device and environment | Behavior on other generations, kernels, firmware, or workloads |

Use the trace `Vulkan requirement -> PanVK implementation -> test coverage ->
hardware execution` when applicable. Collect evidence for each link
independently, mark missing links as gaps, and scope every result to its
revision, configuration, API version/extensions, and test or device conditions.
The specification defines the contract; it is never evidence that PanVK meets
it.

Keep the following distinct: **enumerated**, **reported**, **enabled**,
**implemented**, **exercised by a test**, and **validated on hardware**. A
positive feature bit or extension string proves only the corresponding
reporting path. Confirm all conditions and the actual execution path before
claiming support.

Capability matrices must keep support status and evidence quality as separate
dimensions:

- **Support status:** `SUPPORTED`, `PARTIAL`, `UNSUPPORTED`, or `NOT VERIFIED`.
  This describes the implementation only for the recorded API scope,
  configuration, and target.
- **Evidence quality:** `Confirmed`, `Observed`, `Hypothesis`, or `Unknown`.
  This describes how well the stated claim is established, not how much of the
  feature is implemented.

Record API reporting, test coverage, and hardware execution independently.
A hypothesis cannot establish support; one passing test establishes behavior
only for its covered case. State the evaluated API version/extensions,
architecture, backend, and relevant conditions.

### Object and device state

When relevant, cover instance, physical device, device, queues, command pools
and buffers, pipeline cache, query pools, and auxiliary objects. Trace creation,
initialization, use, synchronization, destruction, and partial-initialization
failure cleanup. Check ownership and allocator rules instead of assuming
objects follow identical lifecycles.

### Graphics pipelines and rendering

Investigate the actual support and implementation for pipeline layout and
shader stages; vertex input and input assembly; tessellation and geometry;
rasterization; multisampling; depth/stencil; color blending; dynamic state;
render passes, subpasses, and framebuffers; and dynamic rendering. Verify each
stage and option independently for the target revision and architecture.
Include multiview and feedback-loop behavior when within the API scope of the
investigation; do not infer their support from render-pass or dynamic-rendering
support.

Trace pipeline creation through shader preparation and state emission to draw
recording and submission. Separate Vulkan validation, pipeline compilation,
command generation, and hardware execution. Do not infer a supported stage or
dynamic state from another stage or from a feature bit alone.

### Compute pipelines and dispatch

Trace compute shader creation, pipeline layout, descriptor and push-constant
setup, workgroup configuration, dispatch recording, resource visibility, and
completion. Verify any architecture-specific limits and dependencies. Keep
compute queue availability distinct from the ability to execute a particular
shader or synchronization pattern.

### Descriptors, queries, and auxiliary API

For descriptor set layouts, pools, sets, updates, binding, dynamic offsets,
push descriptors, descriptor indexing, buffer/image views, and samplers,
follow the full path from Vulkan validation to the state consumed by commands
and shaders. Verify optional and extension-defined behavior individually,
including sampler YCbCr conversion when relevant.

For queries, occlusion, timestamps, events, conditional rendering, and other
auxiliary APIs, confirm the applicable API version/extension, implementation
path, execution conditions, and test coverage. Do not infer availability from
related query types or from a shared object definition.

## Shader and Kraid integration boundary

Trace the path actually selected in the audited revision:

- SPIR-V entry, validation, and conversion to NIR.
- PanVK NIR options and transformations, including stage- or
  architecture-specific lowering.
- Compiler/backend selection and the call site that provides inputs,
  architecture/model information, options, and resource metadata.
- Return values and compiled artifacts consumed by PanVK pipelines.
- Error handling and the tests that reach this path.

Do not presume that Kraid is enabled or selected for PanVK. Verify the build
configuration, runtime/backend selection, and call sites before making that
claim. This skill owns preparation, selection, and integration contracts; the
[Kraid compiler skill](../kraid-compiler/SKILL.md) owns compiler-internal
translation, passes, scheduling, register allocation, spilling, and ISA
generation. Include exact interface evidence in a handoff, rather than
repeating the compiler's internal analysis here.

## Resources, memory, and lifecycle

Trace buffers, images, views, samplers, allocations, memory types/heaps,
binding, mapping, GPU virtual addresses, cache behavior, aliasing, image
layouts, tiling/modifiers, metadata/compression, and import/export only as
relevant to the issue. For each resource, follow:

### Resource lifecycle

| Resource | Creation | Allocation | Binding | Use | Synchronization/visibility | Destruction | Test/evidence |
|---|---|---|---|---|---|---|---|
| Concrete Vulkan resource | Entry point and state | Allocator/path | Binding contract | Consumer | Actual mechanism and conditions | Lifetime path | Exact test or gap |

Include these resource and feature families in the inventory when applicable;
their presence here does not imply PanVK support:

| Area | Check |
|---|---|
| Memory | Sparse resources, external memory, and protected memory |
| Synchronization | External semaphores and external fences |
| Image and sampler | Sampler YCbCr conversion |
| Rendering | Multiview and feedback loops |
| Robustness | Robustness features and related API/extension behavior |

For each relevant item, establish whether it is in scope for the API version,
whether PanVK implements it, its extension/property and shared-infrastructure
dependencies, available tests, hardware validation, and known limitations.
Mark out-of-scope items not applicable rather than implying support.

Keep Vulkan memory requirements and semantics separate from userspace
allocation, Panfrost resource helpers, kernel-managed memory, and platform
interop. For external resources, verify handle type, ownership, metadata,
modifier, and synchronization contracts end to end; never infer layout or
metadata from a handle's incidental representation.

## Synchronization and command submission

For barriers, events, binary/timeline semaphores, fences, Synchronization2,
queue-family ownership transfers, and host synchronization, establish:

1. The Vulkan execution and memory-dependency guarantee.
2. How PanVK records and translates that dependency.
3. The backend command/job or queue mechanism actually used.
4. The kernel interface involved and its matching version, if any.
5. Completion, signaling, error, timeout, and recovery behavior.

Distinguish execution dependencies, memory dependencies, cache flush/invalidate,
visibility, and completion. Do not conflate JM with CSF or assume their
submission semantics are interchangeable. Route kernel/UAPI semantics to a
verified kernel specialist; keep the PanVK-to-kernel contract and its evidence
in this investigation.

Reconstruct the actual execution path for the target rather than mapping a
submission model to a GPU generation by assumption:

```text
Vulkan command recording
  -> PanVK command construction
  -> submission preparation
  -> userspace/kernel interface and matching UAPI
  -> verified CSF or JM queues/jobs and dependencies
  -> GPU execution
  -> completion, signaling, and error handling
```

Confirm the structures, queue mechanisms, interface, firmware dependencies,
and completion/error path in sources applicable to the target revision and
platform. Record which steps are not applicable or remain unknown; hand off
kernel protocol details only to a verified specialist.

## WSI and presentation

Trace surface creation, swapchain creation, image acquisition, present modes,
presentation, synchronization, and buffer import/export. Keep Android and Linux
paths separate, including their window-system, loader, allocator, and
platform-specific constraints. Confirm the actual WSI implementation and
build/runtime configuration for the target platform. A successful offscreen
test or ICD load does not establish swapchain or presentation correctness.

## Panfrost integration reference

Inspect only the Panfrost components needed to explain a PanVK contract:
shared device/GPU information, libraries, GenXML and command helpers, NIR
integration, resource/memory helpers, or kernel-facing abstractions. Verify
which pieces are actually shared in the audited revision. Call out meaningful
differences between Gallium and Vulkan instead of transferring behavior across
frontends. Do not turn this skill into a general Gallium implementation guide.

## Mali generation and backend compatibility

Build conclusions per applicable model and source revision; do not generalize
from the G615 baseline. Check architecture dispatch, hardware feature
availability, execution model (including JM versus CSF), formats and layouts,
synchronization, kernel/UAPI, firmware, and platform constraints separately.
Record whether a result is revision-bound or verified across named revisions.

| GPU/model | Pan architecture | Frontend/backend | Feature or path | Conditions | Kernel/UAPI | Test and evidence | Support status | Evidence quality |
|---|---|---|---|---|---|---|---|---|
| Exact target | Verified value | Verified configuration | Specific operation | Gating conditions | Matching interface/version | Source and test | Supported, partial, unsupported, or not verified | Confirmed, observed, hypothesis, or unknown |

Do not infer cross-generation compatibility from a shared `panvk_vX` helper,
common API structure, successful build, or feature enumeration.

## Investigation and validation workflow

### Failure classification

Classify the first observable failure at its actual stage; do not collapse
multiple stages into a generic `Vulkan failure`.

| Category | Stage |
|---|---|
| Vulkan validation error | API validation or object/parameter checks |
| Shader compilation failure | SPIR-V/NIR processing or backend compilation |
| Command construction failure | PanVK command recording or command generation |
| Submission failure | Queue submission or userspace/kernel handoff |
| GPU execution error | Execution after successful submission |
| Synchronization failure | Dependency, visibility, wait, signal, or completion behavior |
| Presentation failure | Surface, swapchain, acquire, or present path |

For each diagnosis, record the error/message, reproducible conditions and
environment, involved components, the last stage confirmed successful, and
the first stage with an observed failure. Keep the suspected root cause as a
separate hypothesis until evidence confirms it.

1. **Scope.** Identify the failing/desired Vulkan behavior, platform,
   architecture, and primary layer. Record observed behavior separately from
   the proposed cause.
2. **Provenance.** Record repository and Mesa revisions, worktree state,
   `sources.lock`, profile, patch series when applicable, and relevant runtime
   environment. Mark modified source files.
3. **Locate.** Search the checked-out tree for the entry point, implementation,
   dispatch, state, and tests. Confirm each path and symbol in this revision.
4. **Trace.** Follow the operation through its conditions, interfaces,
   side-effects, ownership, and failure handling. Trace beyond PanVK only as
   far as evidence requires.
5. **Classify.** Record facts, observations, hypotheses, and unknowns. Keep
   advertised support separate from execution and validation.
6. **Test narrowly.** Select the smallest relevant static check, unit test,
   CTS case, build target, or authorized hardware test. State what it can and
   cannot establish. Do not run hardware tests without a supported, authorized
   device and bounded procedure.
7. **Change safely.** If a code change is requested, inspect existing diffs,
   define the matching patch family and regression test, and follow `AGENTS.md`.
   Do not edit protected source trees, apply patches, or commit without
   authorization.
8. **Report.** Give the path/symbol and evidence for conclusions, exact
   commands and actual outcomes, limitations, and the next verifiable step.

Keep these validation categories separate:

- Static source audit.
- Build and link.
- Automated/software tests.
- Functional execution on hardware.
- Stability, profiling, and benchmarks.

Report gates as `PASS`, `FAIL`, `BLOCKED`, or `NOT EXECUTED`. Never claim an
unrun test passed, infer runtime correctness from a build, infer feature
execution from enumeration, or make performance claims without a controlled
comparison. Use the repository's build-validation workflow for build/package
issues and a verified testing specialization for test execution or profiling.

## Evidence and traceability records

Use the smallest tables that preserve the relevant chain. Mark unavailable
fields as unknown or not applicable rather than filling them by assumption.

### Vulkan feature traceability

| Vulkan feature | API entry point | PanVK file/symbol | Conditions and scope | Hardware dependency | Generation/backend | Support status | Evidence quality | API report | Test coverage | Hardware result | Source and result |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Exact feature | Query/enable/use paths | Verified implementation | Version, extension, configuration | Verified dependency or unknown | Exact model and JM/CSF path | Supported, partial, unsupported, or not verified | Confirmed, observed, hypothesis, or unknown | Reported/not reported/not checked | Exact case or gap | Exact device/result or not run | Revision, file/symbol, command/result |

### API-to-hardware traceability

| Vulkan operation | PanVK path | Internal state | Command generation | Kernel interface | Hardware mechanism | Evidence/status |
|---|---|---|---|---|---|---|
| Exact operation | Call chain | Relevant objects/state | Actual commands or unknown | Matching interface or N/A | Verified mechanism or unknown | Revision and evidence |

### Environment and provenance

| Repository/revision | Worktree | `sources.lock`/profile | Host/toolchain | GPU/architecture | Kernel/UAPI | Firmware | Tests/limitations |
|---|---|---|---|---|---|---|---|
| Exact identifiers | Clean or specific modifications | Exact inputs | Recorded values | Model and architecture | Version or unknown | Version or unknown | Commands, outcomes, gaps |

## Completion criteria

An investigation or change is complete when:

- The question and primary fault domain are explicit.
- Revision, configuration, worktree caveats, and target generation are recorded.
- The relevant Vulkan-to-PanVK path and cross-component contracts are traced.
- Feature reporting, implementation, testing, and hardware validation are not
  conflated.
- Findings distinguish evidence from hypotheses and unknowns.
- Cross-skill boundaries and handoffs are precise.
- Required tests were run or clearly marked as blocked/not executed.
- Changes follow repository authorization; Mesa driver changes use patches,
  while other project files use direct edits.
- Remaining risks and a verifiable next step are reported.
