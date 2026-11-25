# W03 experimental campaign — ready for execution

**Status:** queued as research specifications only; no new Work run has been confirmed. Preserve the two v0.2 manuscripts and evidence. Do not rewrite the master until results are independently reviewed. Use W03 IDs to avoid collisions with earlier Chat and Work experiment IDs.

## W03-A — Adaptive heterogeneous BESS compression (critical)

Freeze synthetic development and held-out stress seeds and model specifications. Implement nested shared-mode group splitting with individual allocation/SOC, full-model valid outer lower bound and validated feasible incumbent. Baselines: tuned full HiGHS MILP, LP with independent feasibility and mutual-exclusivity checks, fixed grouping, proportional grouping and symmetry quotient where applicable. Stress unequal efficiency/terminal tolerance, unbalanced SOC, reserve floors, heterogeneous power and energy limits, negative prices, outages, forced opposing modes. Measure end-to-end time to valid feasible U and prescribed U−L, candidate quality, presolve, build time, reconstruction, verification, fallback, scaling and failure. A tight LP or no net speedup is a legitimate null result.

## W03-B — Formal verification (critical)

Formalize balanced lift (capacity, sum, rate, directional cycling identity), exact projection/reconstruction, unequal-efficiency zero-throughput obstruction and terminal-tolerance inequality. Pin Lean/toolchain, expose definitions and dependencies, check final statement scope, record axioms, compile and run mutation/negative controls. If Lean unavailable, provide exact rational tests and proof statements only; do not claim machine-checked proofs. Also carry a simple exact candidate/certificate checker with corrupted witnesses.

## W03-C — Structural AC-OPF (high)

Pin PGLib normal and stressed cases at multiple sizes. Compare tuned nonlinear baseline, warm start and an implementable structure-aware candidate, e.g. separators or chordal sparsity. Equal compute and deadline, independent AC residual/limit checks at both branch ends, valid bound separated from feasible cost, full overhead and failures. Static OPF is not SCOPF. Do not claim proof-derived speedup without explicit transfer.

## W03-D — Unit commitment (high)

Pin PGLib-UC cases at multiple scales. Compare strong formulation/solver versus generator grouping, adaptive decomposition or valid cuts with matched deadlines and histories. Report incumbent and bound trajectories, starts, minimum times, ramps, reserve, validated feasibility, compute and failure. Distinguish UC from SCUC; network/contingencies require explicit extension.

## W03-E — Forecast-aware computational load/BESS (high)

Reproduce Work's E05 null result if inputs available, then use rolling imperfect forecasts, ramp/recharge constraints, terminal and ride-through reserves, battery outages and competing services. Strong forecast-aware rule vs optimized policy with equal information. Track unserved energy, useful service, losses, wear proxy, peak imports, reserve and fallback. Perfect foresight is a bound, not a deployable comparator.

## Common acceptance and delivery protocol

1. Freeze model, data hashes, seed split, baseline tuning budget, numerical tolerances, hardware and deadlines before held-out evaluation.

2. Use identical scenarios, information, feasible set and common safety fallback. Independently validate each returned decision; log rejected points and timeouts.

3. Report full end-to-end latency, objective, feasible incumbent, valid lower bound where available, failures, uncertainty and complete denominators. Stratify normal and stressed cases; do not substitute variable counts for runtime.

4. Deliver code, pinned data/license, solver settings, environment, raw results, checks, README, SHA-256 manifest, claim-evidence ledger, and editable experiment report. Identify unrun studies and exact blockers; never invent results.

5. Start with A/B; then C/D/E as feasible. Independent review precedes promotion into v0.3. No production deployment or national-dollar extrapolation.

## Register

| ID | State | Publication gate |
|---|---|---|
| W03-A | Specified, not confirmed launched | Held-out feasibility and matched-baseline benefit |
| W03-B | Specified, not confirmed launched | Actual proof/checker execution and statement match |
| W03-C | Specified, not confirmed launched | Validated AC and equal-budget comparator |
| W03-D | Specified, not confirmed launched | Validated chronological constraints and bounds |
| W03-E | Specified, not confirmed launched | Equal-information policy comparison |
