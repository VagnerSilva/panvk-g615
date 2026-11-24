# Operational audit and documentation approval

## Identity and limits

Plan: [plan.md](../plan.md), phases 0..8 grouped into the four authorized
blocks. Project baseline during generation:
`4f70daa6c2ffde2d509c5a9961219871f57084d5`, branch `feat-migration`.
Mesa pin: `13baeb70c066a9f82d2bcfb29f06e4865212affa`, `27.0.0-devel`.
Input series in the lock: `3e20d28a3753e671f6cbfe164372e71b55ecf407dec039f56c05232c53bf2060`.
These values identify the generation, not a tested binary.

Scope: Moto G86 / Mali-G615 MC2 / MT6878 / Android16 pending confirmation,
with complementary glibc in an Android chroot. The original generation added
only new documents; the plan, Mesa sources, profiles, neighboring skills,
and historical evidence were preserved. No build, installation, profiler,
adb access, or physical benchmark was performed.

The [inventory](performance-baseline.md) records reused resources and gaps.
There are six operational references, the SKILL.md entry, and this report.
No benchmark, production script, or physical baseline was created.

## Controlled exercise method

The exercises use local manifests/logs and explicitly marked **SYNTHETIC**
data. Exercise 1 runs host analysis of existing functional evidence, not the
shader again. Checking options and guards is static reading, not runner
execution. Fixture calculations and assertions are offline auditing; they
do not validate the ICD or establish autonomous hardware operation.

### 1. Functional test using existing evidence

- Input: [Moto manifest](../../../../validation/mesa27-large-draw-initializer-fix.json).
- Procedure: select the test by function in [functional testing](functional-testing.md);
  read identity, matrix, and `notValidated`.
- Expected interpretation: 4 sizes x direct/indirect x 8 runs = 64/64
  historically reported checks, plus additional tests with their own limits.
  Class HISTORICAL_REPORT, not REPRODUCED during this generation.
- Do not approve current AHB/presentation/performance. Plan for future execution:
  the corresponding tessellation/large-draw case, an identified ICD, and approved
  limits; do not run every test merely because the manifest exists.

### 2. Prepare a reproducible benchmark

- Question: GS pass-through cost on the Moto, not gaming FPS.
- Plan: `workload-perf`, `ref/gs_pass` cases, `PT_WP_MS=400`, deadline/grace
  60s/3s, five initial alternating A/B pairs, identical workload/ABI/compiler/
  cache, complete reads and checks. Recipe in [benchmarking](benchmarking.md).
- Expected interpretation: options exist in the source; `workload-perf` has
  no CLI case selector, so run the full workload and analyze the relevant cases.
  Unknown timestamp capability blocks execution of this program.
  The `duchamp` CTS runner must not be used on the Moto.
- `ms` is wall time for offscreen frames/submission/readback, not presentation
  or a GPU timing breakdown.

### 3. Interpret frame time

- SYNTHETIC input, ms: `[16,16,16,16,16,16,16,16,16,100]`.
- Expected interpretation: median 16ms, mean 24.4ms, nearest-rank p95 100ms,
  aggregate FPS `1000/24.4 = 40.984`. There is a long tail; do not claim
  stability based on the median's ~62.5 FPS equivalent.
- Ten frames are an arithmetic example, not optimization sampling.
  Without individual frames, p95/p99 remain unavailable.

### 4. Memory bottleneck hypothesis

- SYNTHETIC input: RSS 300->650 MiB, MemAvailable 1200->180 MiB,
  SwapFree 800->100 MiB, tail 20->150ms in the same window.
- Expected interpretation: pressure/paging is a hypothesis supported by
  correlation; none of these values is bytes/s, VRAM, or occupancy.
  Do not assert saturated bandwidth or a leak.
- Control: the same workload with initially healthy memory, correlated
  snapshots and frame times, without killing apps/clearing caches/swap.
  If the tail persists without pressure, the hypothesis weakens. A gate
  dependent on an unavailable counter remains BLOCKED.

### 5. Synchronization problem

- Input: [Moto app/shell report](../../../../tests/README.md).
- Expected interpretation: candidate `d30b7c60...` reports shell release PASS,
  but app UID image creation fails with `VK_ERROR_INVALID_EXTERNAL_HANDLE`
  before release. First causal gate: historical import/metadata FAIL.
- App release/completion is BLOCKED; this does not establish a CSF hang
  or invalid fence. Shell and app results cannot be combined into a WSI PASS.
- Subsequent control: establish import in the same UID first; only then
  release/FD and a workload with readback, using the
  [functional workflow](functional-testing.md).

### 6. Compare two versions

- Input: the current lock versus the Moto manifest from exercise 1.
- Expected interpretation: same Mesa pin, different series (`3e20d28a...`
  versus `7d02a194...`), historical hash `c4532ef9...`, no current loaded hash
  in the lock. Performance comparison is BLOCKED, not a tie or a gain.
- Requires two identified ICDs, the series/compiler delta, the same Moto,
  context/ABI/cache, and real samples. MC6 profile data does not fill Moto gaps.

### 7. Evaluate an optimization

- SYNTHETIC input, five paired runs, time in ms:
  A=`[10,10.2,9.8,10.1,9.9]`, B=`[8,8.2,7.8,8.1,7.9]`.
  Control medians 5->5.6ms; both declared functional PASS only for the
  fixture. Criteria defined in advance: minimum gain 10%, maximum control
  degradation 5%.
- Expected interpretation: medians 10->8ms, time reduction 20%, speedup 1.25x;
  min/max A 9.8/10.2, B 7.8/8.2. Control degrades 12% > 5%:
  **FAIL optimization approval**, despite the primary metric improving.
- Noisy real samples or missing controls must remain INCONCLUSIVE/BLOCKED;
  never turn a fixture or a fast run into a Moto improvement.

## Verification and corrections

Generation validation: frontmatter, files, links, and whitespace for all new
documents; seven host exercises with evidence/options/calculation assertions;
complete review of additions and independent operational review.
Executed commands/results are recorded below. No duplicate benchmark suite
was added.

Executed results:

- `python3 audit_gpu_skill.py` (temporary session script, executed by absolute
  path, not production tooling): **7 tests, 0 failures**; **8 documents,
  70 resolved links**, frontmatter/newlines/whitespace PASS. Assertions consult
  local sources and calculate the fixtures above.
- `git diff --check`: exit 0. Because the additions are still untracked,
  the session validator also checks whitespace directly in every new document;
  it does not depend on a tracked-file diff.
- Independent reviewer `gpu-skill-audit`: read the eight original documents
  and checked the seven exercises and operational usability; no significant
  findings or minor suggestions. All seven verdicts were considered actionable
  under the documented prerequisites. No build, upload, or hardware in the review.

Corrections incorporated during construction:

- Timestamp prerequisite gate for programs that do not safely skip.
- Separate cold-load/steady-state, best-of-3/median-of-5/independent runs.
- Disable historical tess A/B in the first run with `PT_TESS_AB=default`.
- Block Moto CTS instead of bypassing `duchamp`/musl.
- Require log preservation and no uploads before using PanProbe.
- Treat AHB import, release, FD, readback, and WSI as separate gates.
- Explicitly block unavailable metrics and incomplete comparisons.

Language correction: the eight generated documents were translated into
English at the user's request. Commands, references, criteria, and historical
results were retained; the supplied plan remains unchanged. The independent
review above applies to the original generation, not a new review of the
translation.

## Coverage of plan criteria

| Criterion | Procedure/evidence |
|---|---|
| MC2/Moto scope and separate history | SKILL.md; baseline/inventory; exercises 1, 5, 6 |
| Functionality and regressions | functional-testing.md; exercises 1, 5 |
| Reproducible benchmarks and classified metrics | benchmarking.md, profiling.md; exercises 2, 3 |
| Domain profiling and operational diagnosis | profiling.md, bottleneck-analysis.md; exercises 4, 5 |
| Traceable optimization, baseline, and history | optimization-validation.md, performance-baseline.md; exercises 6, 7 |
| No metric assumed available | Prerequisite gates and profiling table; compute/bandwidth/thermal gaps |
| Operational audit | Exercises above and final results below; not physical qualification |

## Generation gates

| Gate | Status | Evidence/limit |
|---|---|---|
| Inventory and documentation traceability | PASS | Local sources and boundaries recorded |
| Structure/links/whitespace | PASS | 8 documents, 70 links; direct validation of additions |
| Seven offline exercises | PASS | 7/7; historical/synthetic data without hardware |
| Independent review | PASS | Original eight documents and seven exercises; no significant findings |
| New ICD build/ELF/package | NOT EXECUTED | Outside the generation scope |
| Physical functionality/stability | NOT EXECUTED | No execution authorized during this generation |
| Physical benchmarking/profiling | NOT EXECUTED | No execution authorized during this generation |
| Moto performance baseline | BLOCKED | Not established by the inventoried material |
| Final skill approval | BLOCKED | User approval after review |

Next physical gate, when authorized: confirm context/ICD and a focal functional
test; qualify metrics and a Moto A/B campaign separately. Do not execute that
gate as a side effect of generating the skill.
