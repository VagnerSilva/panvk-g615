# Responsibility and routing matrix

Delivery 2: responsibilities and routing. The [central skill](../SKILL.md)
accepts objectives without known paths; the names below link to real entries.
This matrix details decisions, not specialist procedures.

## Responsibility and acceptance

| Objective | Primary owner | Acceptance / domain output | Do not assume |
|---|---|---|---|
| Correct translation, IR, passes, RA/spill or ISA; run compiler-local tests | [kraid-compiler](../../kraid-compiler/SKILL.md) | Compiler invariant and regression identified | Local tests prove Moto behavior |
| Implement/correct Vulkan functionality and the necessary shared Panfrost interface | [panfrost-panvk](../../panfrost-panvk/SKILL.md) | API contract, compiler selection/input/output and driver path | Shader/sync symptoms prove a Kraid or kernel cause |
| Correct ABI/UAPI/ioctl, CSF, memory/VA and sync_file/KCPU/context | [mali-kernel-platform](../../mali-kernel-platform/SKILL.md) | Platform contract and edit sites; revision/context-bound evidence | Another DDK, JM, Panthor or device is equivalent |
| Prepare/diagnose builds, host/target dependencies, ELF/loader and ICD packages | [panvk-build-validation](../../panvk-build-validation/SKILL.md) | Identity, provenance, toolchain and artifact verified in executed gates | Build/link/ZIP proves functionality |
| Reproduce regressions, execute functional/CTS tests, measure stability/performance | [gpu-testing-profiling](../../gpu-testing-profiling/SKILL.md) | Bounded experiment, data and scoped conclusion | Execution implies authorization or a known cause |
| Coordinate global Kraid integration, Mesa migration or shared compatibility | [mesa3d-mali-expert](../SKILL.md) | Explicit interfaces/dependencies and architectural decisions | A migration specialist or wider hardware support exists |

## Disambiguation by objective and first stage

| Request without internal paths | Decision |
|---|---|
| "The shader fails to compile" | Read the error/stage. NIR/Kraid translation: compiler. SPIR-V/NIR preparation, selection or pipeline: PanVK. Toolchain/link: build. Without evidence, request the error and operation, not a directory |
| "Rust cannot compile the driver" | Build first for rustc, dependency, configuration or link failures; do not treat these as shader-compilation failures |
| "Memory is incorrect" | Vulkan resources/layout/binding: PanVK. Platform VA/import/ioctl/cache/fences: platform. Measuring pressure/bandwidth: GPU. Without a stage, investigate evidence before attributing a cause |
| "Synchronization fails" | Vulkan barriers/semaphores/visibility: PanVK. sync_file/KCPU/CSF ABI: platform. Reproduction/stability request: GPU; hand off the cause later |
| "I need to optimize Vulkan" | Open-ended request: measure with GPU before choosing an algorithm/layer. Proven localized correction: implementation owner, followed by GPU comparison |
| "The ICD does not load" | ELF/ABI/symbols/dependencies/package: build. Mali access permission/context: platform. Vulkan enumeration/features/discovery: PanVK, according to the first error |
| "Implement full Gallium support" | Central bounds the interfaces; PanVK is not a full Gallium guide. Declare the gap and obtain a decision without inventing a skill |
| "Run JM/Panthor on another GPU" | Central declares the request outside the frozen operational target; specialists may analyze documented boundaries, not qualify a new target without approval |

The scope gate precedes execution ownership: in the last case, central is
primary, not GPU as a candidate executor. Unknown physical identity does not
block documentary classification within the target; it blocks execution
dependent on that confirmation.

## Conditional dependencies

Arrows are dependencies, not a list of skills to load in advance.

| Evidenced case | Required sequence |
|---|---|
| Kraid translation fails; correct and validate a Mesa candidate | Compiler → build; GPU only if hardware behavior is an acceptance criterion and execution is authorized |
| Incorrect CSF ioctl layout; caller also affected | Platform → PanVK only for the caller contract → build → focused GPU when required/authorized |
| New Vulkan functionality depends on new translation | PanVK defines contract → compiler handles internals → PanVK integrates return → build → GPU when required/authorized |
| Benchmark two identified ICDs with a valid handoff | GPU only; no rebuild or implementation-owner activation without a cause |
| Benchmark without valid candidate identity/provenance | GPU defines question; build establishes missing artifact/identity → GPU, without hardware execution before prerequisites |
| Global Kraid integration | Central defines interfaces/compatibility → PanVK for consumers and compiler for backend as needed; build/tests only for changes requiring them |

## Handoff contract

Record objective, owner and justification, evidence versus hypothesis,
conditional dependencies/order, scope, permissions and next step. The
specialist discovers files/symbols; the subsequent handoff carries those
locators, revision, ABI/configuration, artifact/context, tests and gates
without repeating the investigation.

Verify availability and load the current entry before using procedures.
If unavailable/out of scope, declare the gap and coordinate verified guidance
only. No return to central implies a loop or activating every skill.
Real technical conflicts require a decision before the affected action.
Routing homologation does not change code/hardware approval.
