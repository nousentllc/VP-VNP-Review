# W04-A · Battery grouping, LP recovery and unrestricted commitment of device modes

## Decision

The adaptive grouping hypothesis failed the two-second comparison with LP-informed repair. Grouping reached the certified-gap target on exactly the same 54 of 72 cases as raw LP alone. The other 18 cases were the forced-opposition cohort, where grouping delivered zero practical wins, eleven ties and seven losses against repair at two seconds. The matched fallback-start ablation reached target in all repeats on one forced case, whereas the grouped-transfer arm achieved none. Retire a claim that grouping improves this tested pipeline over LP repair.

Within those 18 hard cases, grouping beat the direct full MILP five times and lost twice at two seconds. All five wins occurred among the six 12×16 forced cases. On those same six cases grouping lost all six comparisons against LP repair, making the choice of comparator decisive. Transferring a grouped start improved two forced case medians over the matched fallback transfer at two seconds (16 ties). The paired median cost change was zero. A portfolio branch based on grouping would need different prospective evidence.

## Study design and denominator

Seventy-two synthetic battery instances cross six unused generator seeds with three sizes (4×8, 8×12, 12×16 devices×hourly periods) and four deliberately constructed operating regimes. A single common fallback is physically feasible on every case. Ordinary and negative-price/outage seeds alternate between an exact device endpoint and a 3.5%-of-capacity endpoint tolerance. Interchangeable and forced-opposition cases use cyclic individual endpoints. In the forced family the grid exchange is fixed to a known physically feasible profile; paired devices can be required to move in opposite directions. Its prevalence in this panel bears no relation to field frequency. Shared direction binaries reduce only direction freedom. Power, losses, SOC, endpoints, availability, reserve floors, grid bounds, ramp and wear remain individual or physical as applicable.

HiGHS 1.12 with presolve enabled ran serially at one thread per arm on arm64 macOS. Each case has three rotated repetitions of five methods. The two-second monotonic clock includes validation of the fallback, optimization matrix construction, presolve/solve, start transfer and checking. Input decoding and raw file serialization run outside the per-trial clock. The per-case count requires the target in all three repetitions. Fixed-clock comparisons use paired case-median dispatch cost. A lower cost is better. A practical win/loss requires a difference exceeding 0.1% of max(1, absolute common fallback cost). Bootstrap intervals for the median resample the six seed labels with all sizes within a cohort (5,000 draws). They describe synthetic panel sensitivity. Repetitions share a machine and identify clock variation, not new problem instances.

Development evaluated both start strategies at 10%, 20% and 30% of the two-second budget on three W03 forced cases, 18 trials total. None hit the prescribed gap. The shared 30% choice produced the largest mean development fallback-relative quality gain (2.502%; 10% and 20% both 2.027%). The 600 ms cutoff budgets the *entire* LP and candidate-generation prefix. The LP policy tries a sign-fixed solve, followed by a repair MILP fixing only unambiguous active LP directions. Grouping starts with one sign per period and bisects each group by member LP net power in the period of maximum dispersion. Each restricted solve receives at most 300 ms, within the same 600 ms prefix. The final unrestricted solve restores all device-hour binary choices, accepts a checked complete primal vector if available, and can go beyond it. The matched transfer ablation keeps the identical grouping policy and best externally validated incumbent, but transfers the common fallback to the final unrestricted solver. Both LP-first start policies can stop after an admissible LP reaches target.

The target is U−L ≤ 0.00002 + 0.001 max(1, |U|). All U values come from physically checked original schedules. Online L comes from the numerically cushioned unrestricted LP Lagrangian box bound or the unrestricted MIP numerical dual. No restricted solver dual enters the target. The post-run checker evaluates full-LP box certificates exactly over rational representations of stored binary64 coefficients and row multipliers. These certify lower bounds for those stored models. They do not turn MIP search bounds or tolerated physical schedules into exact optimality proofs. The normalized primal integral uses the same offline LP bound for all arms of a case and the common fallback trajectory until first improvement (smaller is better). The two-second cap is assigned to every target miss.

## W03 reproduction

All 450 W03-A timing trials were rerun from the preserved W03 pipeline and reanalyzed with the reviewer's fixed-clock rule. Reanalysis of the historical trace agrees exactly with all archived six-clock arrays and counts. The fresh W03 replay again reached the target on 20/24 cases for the full MILP, LP-recovery and adaptive arms and on 18/24 for LP alone. At 250 ms on the six historical forced-opposition cases, adaptive vs direct MILP gave 3 better, 2 ties, 1 worse in both archives. At 2 s the historical trace had 0/6/0, while the fresh trace had 2/4/0 using the W03 review's cost tolerance of 0.00001. Fixed-clock cost outcomes are sensitive to the run, even with stable all-repeat hit counts. W04 has a different prospective practical tolerance, new seeds, and actual unrestricted warm starts. See results/w03_reproduction.json and results/w03_replay.jsonl.gz.

## Held-out results

Cases reaching the target in all three repeats (18 per column; synthetic costs throughout).

| Method | Ordinary | Negative price / outage | Forced opposition | Interchangeable | All / 72 |
|---|---:|---:|---:|---:|---:|
| Full MILP | 14 | 17 | 0 | 14 | 45 |
| LP only | 18 | 18 | 0 | 18 | 54 |
| LP repair → full | 18 | 18 | 0 | 18 | 54 |
| Group → full | 18 | 18 | 0 | 18 | 54 |
| Group → fallback start | 18 | 18 | 1 | 18 | 55 |

Median capped target latency (milliseconds). Each entry is the median of the 18 case medians. A miss contributes 2,000 ms. A short latency in an easy cohort primarily measures solving or validating the LP.

| Method | Ordinary | Negative price / outage | Forced opposition | Interchangeable |
|---|---:|---:|---:|---:|
| Full MILP | 398.0 | 215.2 | 2000.0 | 341.8 |
| LP only | 24.1 | 18.4 | 2000.0 | 23.5 |
| LP repair → full | 22.5 | 19.1 | 2000.0 | 25.0 |
| Group → full | 26.7 | 17.1 | 2000.0 | 23.6 |
| Group → fallback start | 23.5 | 20.1 | 2000.0 | 26.5 |

### Matched dispatch quality and uncertainty

Forced-opposition results. Δ is the grouped-start cost minus the comparator at the same clock. Units are the same synthetic cost units as the dispatch model. W/T/L uses each case’s practical threshold. CI is the 95% six-seed block bootstrap interval for the case median Δ. See contrasts.csv for all four strata and their paired means.

| Comparator | Clock (s) | Cases | W/T/L | Mean Δ | Median Δ | 95% CI |
|---|---:|---:|---|---:|---:|---|
| Full MILP | 0.25 | 17 | 3/12/2 | -0.708 | 0 | [0, 0] |
| Full MILP | 2.0 | 18 | 5/11/2 | -2.35 | 0 | [0, 0] |
| LP repair → full | 0.25 | 17 | 1/8/8 | 3.88 | 0 | [0, 7.67] |
| LP repair → full | 2.0 | 18 | 0/11/7 | 2.93 | 0.000376 | [0, 1.32] |
| Group → fallback start | 0.25 | 16 | 1/15/0 | -0.192 | 0 | [0, 0] |
| Group → fallback start | 2.0 | 18 | 2/16/0 | -0.945 | 0 | [0, 0] |

All 72 cases, grouped-start vs each comparator, practical wins/ties/losses at each scored clock. Consult lp_strata.json for admissible and inadmissible LP strata and missing-pair counts.

| Comparator | 50 ms | 100 ms | 250 ms | 500 ms | 1,000 ms | 2,000 ms |
|---|---|---|---|---|---|---|
| Full MILP | 33/32/0 | 33/33/1 | 34/34/3 | 27/43/1 | 19/51/1 | 10/60/2 |
| LP repair → full | 4/58/2 | 3/60/4 | 3/59/9 | 0/60/11 | 0/61/10 | 0/65/7 |
| Group → fallback start | 1/63/2 | 1/62/4 | 2/67/1 | 1/68/1 | 2/68/0 | 2/70/0 |

### How the policies used their time

Forced-opposition cohort (54 runs per arm). First improvement is time to a strictly lower validated cost than fallback, summarized only on runs where it occurred. Restricted-prefix time excludes the preceding LP and includes group/sign model construction, solves, checks, and transfer where applicable. The integral is the median of three-repeat case medians with positive denominator.

| Arm | Runs with improvement | First improvement, median ms | Restricted prefix, median ms | Normalized integral | U at 2 s still fallback (runs) |
|---|---:|---:|---:|---:|---:|
| Full MILP | 23 | 1062.6 | — | 1.000 | 31 |
| LP only | 0 | — | — | 1.000 | 54 |
| LP repair → full | 38 | 185.5 | 590.9 | 0.425 | 16 |
| Group → full | 34 | 312.9 | 575.6 | 0.807 | 20 |
| Group → fallback start | 32 | 326.9 | 574.7 | 0.887 | 22 |

### Start acceptance and failure traces

Actual solver confirmation requires a feasible-start objective in the HiGHS log that agrees with a previously validated schedule, and original device-hour mode count and unrestricted matrix dimensions.

| Arm | Unrestricted calls | Feasibility confirmed | Nonfallback feasible starts |
|---|---:|---:|---:|
| Full MILP | 216 | 216 | 0 |
| LP only | 0 | 0 | 0 |
| LP repair → full | 53 | 53 | 37 |
| Group → full | 54 | 54 | 31 |
| Group → fallback start | 54 | 54 | 0 |

Replayed 3,019 retained trajectories across 1,080 trials. 215 returned or retained schedules failed physical validation. The maximum accepted residual was 8.51e-12 against a 2e-6 cutoff. 72 exact LP bound evaluations passed the stored-incumbent check. The worst discrepancy between a full-solver start acknowledgement and its independently checked source cost was 4.34e-08. All 72 fallback controls passed. All 72 corrupt charge and all 72 corrupted transferred-state controls were rejected.

Of 1,080 trials, 234 returned after the two-second nominal gate, with maximum wall duration 4.773 s. The score only uses timestamped validations and bounds at or before the gate. HiGHS presolve, model construction and return paths can delay interruption. Full elapsed clocks and the identities of late final returns are in trials.jsonl.gz. Solve times include callbacks, and reported validation, solve and transfer columns can overlap. Clock timing, callback sequence and start-induced trajectory changes can vary under concurrent research processes. Start acceptance documents receipt. The matched fallback-transfer comparison is required for performance attribution.

All raw failures and unsuccessful construction or processing statuses are retained. The forced single-group root status histogram across the two grouped arms was {'Infeasible': 102, 'build_exhausted_budget': 2}. For sign-fix and partial-repair statuses see results/start_audit.json. Failed starts for a *restricted* stage need not be feasible in that restriction, even when they are valid original schedules. The full stage always restores the original model. No subset of the synthetic costs was extrapolated to grid revenue, reliability or site economics. The optional larger-than-12×16 panel was deferred before holdout; three timing repetitions ran on one machine. The process RSS is a cumulative process high-water mark and overlapping clock categories cannot yield phase-specific memory.

## Mechanism and timing interpretation

The raw LP returned physically admissible actions and closed the gap on each of the 54 ordinary, negative-price/outage or interchangeable cases in all three LP-only trials. The group-first and repair-first policies therefore skipped every restricted stage in those cohorts. On the 18 forced cases the isolated root presolve identified single-group infeasibility in 18/18 instances. In the timed grouped arms it identified 102 infeasibilities, with two further root constructions exhausting their allotted stage budget. Four grouped runs passed their prefix deadlines without attempting a root. Every one of the 53 attempted fully sign-fixed repairs in this cohort was infeasible. The confidence-only repair retained freedom and supplied 37 nonfallback unrestricted starts. One LP-repair trial exhausted the full clock while building the initial LP. It lacked an unrestricted solve and kept its validated fallback.

Forced-cohort final sources in the 54 grouped-start trials were a restricted solve in 17, a later unrestricted improvement in 17, and fallback in 20. The LP-repair arm ended with a partial-sign repair in 33 trials, an unrestricted improvement in 5, and fallback in 16. The normalized primal integral also favored repair on this panel: the paired median group-minus-repair difference was +0.258 (95% seed-block interval +0.164 to +0.289, 18 cases). Its positive sign means that grouped starts spent more of the budget at inferior feasible cost. The measured median first improvement across improving trials was 313 ms for grouping and 186 ms for repair. The time-to-first comparison has different censoring across policies.

The 250 ms forced comparisons omit one case against each full/repair baseline and two against the matched no-transfer baseline because a fallback had not been validated on time in every required run. All three repeats are present in all two-second comparisons. Three trials took longer than 250 ms just to record the initial fallback, including one at 1.287 s. The scheduler contributes substantial variation to the wall-clock evidence. Compare fixed-clock feasible dispatches and bounds, and retain missing actions as such. Dormant arms, especially raw LP, can still retain the common fallback when the LP output itself is physically inadmissible. The design measures a validation-gated score and does not implement a watchdog that guarantees returning control within two seconds.

A separate post-run diagnostic measured 216 standalone presolves on the full LP, full MILP and shared root across all frozen cases. The 18 forced-case median presolve times were 1.58, 3.66 and 2.89 ms respectively. Standalone timings exclude starts, solver work, and construction and differ from in-pipeline measurements. The raw presolve statuses and matrix counts are in results/isolated_presolve.csv.
