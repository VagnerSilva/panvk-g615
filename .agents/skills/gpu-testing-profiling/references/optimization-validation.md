# Comparative optimization evaluation

## Contract before measuring

Use the [baseline](performance-baseline.md). Specify the predicted effect,
primary workload, unaffected controls, metric/unit, and tolerances: minimum
relevant gain, maximum degradation per control, frame tails and memory,
functional checks, and stability cycles. Do not invent an acceptance
percentage after seeing the numbers. Without criteria, analysis is exploratory.

A/B must use the same Moto, kernel/firmware/OS, UID, ABI, API, resolution,
assets, limits, cache, compiler, conditions, and toolchain/configuration,
except for the declared change. Record SHA-256/Build ID for both loaded ICDs.
Series differences must identify the actual delta; if several deltas change,
do not attribute the result to a specific optimization.

Do not automatically apply Mesa patches or replace an installed ICD. Receive
prepared and authorized candidates; use separate paths. Start each run in
a fresh process to avoid previously cached flags/compiler/cache settings.

## Measure and compare

1. Validate functional checks on A and B; errors/mismatches invalidate timings
   for approval even if the candidate is faster.
2. Use the [benchmark protocol](benchmarking.md), including documented warmup
   and 5 initial AB/BA pairs. Cold-load is a separate campaign.
3. Record every sample, exit status, count, condition, and justified exclusion.
   Do not exclude a slow outlier for convenience; preserve discarded data.
4. Aggregate **compatible runs per case**. Record median, dispersion
   (min/max and IQR or standard deviation with the method), and paired
   differences. If individual frames exist, use the same p95/p99 method and
   compare tails.
5. When lower time is better:
   `reduction_% = 100 * (A - B) / A`, `speedup = A / B`, with positive A/B.
   When higher throughput is better: `gain_% = 100 * (B - A) / A`.
   20% less time is not 20% more throughput: in that case it is 25%.
6. Compare dispersion with the effect and thresholds. If AB/BA order,
   thermal drift, cache, or insufficient samples explain the delta, report
   INCONCLUSIVE. Do not claim statistical significance without an appropriate
   method/interval and adequate sampling.
7. Run affected and unaffected functional and performance controls within
   approved limits. Missing required controls means approval is BLOCKED.

## Verdict and gates

| Verdict | Required evidence |
|---|---|
| Reproducible improvement, performance PASS within scope | Compatible identities/contexts, effect above the minimum, documented dispersion without unresolved confounders, controls within tolerance, and functional/stability PASS for the defined cycles |
| Regression, FAIL | Functional failure or degradation beyond the predefined limit; record separately whether primary timing improved |
| INCONCLUSIVE, approval BLOCKED | Valid data, but noise/confounders/quantity prevent a decision |
| Execution/comparison BLOCKED | Missing indispensable baseline, identity, capability, authorization, or environment |
| NOT EXECUTED | Campaign not executed; preparation and offline auditing are not performance measurements |

Do not extrapolate to unmeasured workloads or other GPUs. A gain only in the
primary case with relevant degradation in a control does not approve the
optimization. Kraid statistics, a successful build, and enumeration are
supporting evidence, never substitutes.

## Report

Record baseline/candidate, source delta, question, fixed criteria,
method/samples/dispersion, checks and results per case, confounders, the
first failed gate, and a bounded conclusion. Separate synthetic from measured
data; the [audit exercises](operational-audit.md) do not approve an ICD.
