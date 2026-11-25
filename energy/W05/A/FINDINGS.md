# W05-A · Individually validated LP screening

## Decision

Screening and direct escalation reached the within-two-second target on 48/60 cases in every repeat. The equally screened LP-repair comparator reached 48/60. Native MILP with an independent certificate pass reached 48/60. The prespecified joint improvement gate **failed**. It required at least two extra case hits against each comparator and a strictly positive lower endpoint for both paired seed-block intervals.

## Primary comparison

Four unused seed labels were crossed with three device-by-hour sizes and five stress families. Exactly 24 of 60 cases supplied a prevalidated constructive fallback and 36 did not. Of these 36, twelve were generated from an exogenous exchange corridor without any feasible plan construction. A missing action or inconclusive solve is not model infeasibility. The 900 rows include three rotated repeats and five arms per cell. The family frequencies and four seed clusters are experimental design choices.

| Arm | Cases with all-repeat exact-bound target | Cases with all-repeat action | Cases with all-repeat target and whole function returned in 2s | All-repeat gaps using offline common LP bound |
| --- | ---: | ---: | ---: | ---: |
| Native MILP + independent proof | 48 | 57 | 48 | 48 |
| Full LP alone | 44 | 52 | 44 | 44 |
| LP repair and unrestricted start | 48 | 59 | 48 | 48 |
| Screen and direct escalation | 48 | 58 | 48 | 48 |
| Full-budget native diagnostic | N/A | 58 | N/A | 48 |

The fifth arm solves the native model without an explicit LP proof call. Its solver-reported numerical MIP gap met the target on 51/60 cases in all repeats. Only the separate retrospective column uses a certified bound that another arm may have obtained later. No primary arm receives that bound online. Lower bounds from the LP do not close an integer gap automatically. The primal check uses native units with tolerance 2e-6.

| Stress family (12 cases each) | Native + proof | LP | LP repair | Screen |
| --- | ---: | ---: | ---: | ---: |
| ordinary | 12 | 12 | 12 | 12 |
| negative_outage | 12 | 12 | 12 | 12 |
| forced_opposition | 0 | 0 | 0 | 0 |
| tight_reserve | 12 | 8 | 12 | 12 |
| unknown_exchange | 12 | 12 | 12 | 12 |


## Paired effects and clocks

Effects are screen minus reference. Fixed costs compare case medians over complete triples only. The win/tie/loss counts use the practical input-specific threshold, and the intervals resample four whole seed blocks, 5,000 times. Cases with no observed action at a clock remain missing for that quality comparison. The complete-case denominator must travel with each difference. All six clocks, no-action events and case-level differences appear in the CSVs.

| Comparator | Metric | Pairs | Paired effect | 95% seed-block interval | Practical W/T/L |
| --- | --- | ---: | ---: | ---: | ---: |
| LP repair | Target rate, mean | 60 | 0.000 | [0.000, 0.000] | 0/60/0 |
| LP repair | 250 ms cost, median | 56 | 0.000 | [0.000, 0.000] | 0/53/3 |
| LP repair | 2 s cost, median | 58 | 0.000 | [0.000, 0.000] | 0/54/4 |
| LP repair | Normalized area, median | 24 | 0.000 | [0.000, 0.000] | 6/0/18 |
| LP repair | Capped time (s), median | 60 | 0.000 | [0.000, 0.000] | 23/12/25 |
| Native + proof | Target rate, mean | 60 | 0.000 | [0.000, 0.000] | 0/60/0 |
| Native + proof | 250 ms cost, median | 56 | 0.000 | [0.000, 0.000] | 10/46/0 |
| Native + proof | 2 s cost, median | 57 | 0.000 | [0.000, 0.000] | 1/56/0 |
| Native + proof | Normalized area, median | 24 | -0.005 | [-0.005, -0.005] | 16/2/6 |
| Native + proof | Capped time (s), median | 60 | -0.093 | [-0.099, -0.078] | 48/12/0 |

| Arm | No action / 180 | Fallback retained / 180 | Wall median / p95 / max (s) | Calls over 2 s |
| --- | ---: | ---: | --- | ---: |
| Native MILP + independent proof | 9 | 6 | 0.184 / 1.460 / 1.499 | 0 |
| Full LP alone | 24 | 24 | 0.010 / 0.049 / 0.082 | 0 |
| LP repair and unrestricted start | 2 | 1 | 0.020 / 2.007 / 2.034 | 27 |
| Screen and direct escalation | 6 | 6 | 0.023 / 2.010 / 2.113 | 24 |
| Full-budget native diagnostic | 6 | 6 | 0.170 / 2.011 / 2.031 | 27 |

The primary target clock marks when the individual dispatch and exact outer bound are known inside the worker. Reading solver logs and cleanup can delay synchronous completion. The separately reported return-time target counts exclude any run whose complete worker returned late. This shared arm64 host had no exclusive core or independent hardware replay. Raw monotonic time is one observed schedule. There is no production handoff or physical actuation measurement.

## Mechanism and certificate audit

Both LP-first escalation arms use the same early success test. The test charges unrestricted LP assembly and solve, individual-mode and physical validation, and exact rational certificate calculation. When the LP fails, screening goes immediately to the native model. LP repair first attempts a sign-fixed LP and then a partially fixed MILP. Development gave each method the same two settings and W04 cases. Selected effort/time-share settings appear in protocol/freeze.json. The test compares the resulting policy pipelines; a cost difference cannot be assigned to a faster LP solver.

| Arm | Outer-only target / 180 | Explicit LP then native solve | Accepted native starts / submitted | Median exact bound time (ms) |
| --- | ---: | ---: | ---: | ---: |
| Native MILP + independent proof | 0 | 0 | 72/72 | 4.64 |
| Full LP alone | 132 | 0 | 0/0 | 4.38 |
| LP repair and unrestricted start | 132 | 36 | 34/34 | 4.37 |
| Screen and direct escalation | 132 | 48 | 24/24 | 4.39 |
| Full-budget native diagnostic | 0 | 0 | 72/72 | N/A |

The independent replay checked 2,319 primal witnesses, including 144 that failed the original device tolerances. It independently reconstructed 720 rational multiplier evaluations (60 unique case/multiplier pairs). The largest admitted physical residual was 7.69e-11. Lower values were rounded downward from exact fractions before numerical gap reporting. Each of 60 corrupted output controls failed the physical checker. A separate exact two-binary control exposes the sign error in an invalid reduced-cost lower bound.

For a minimization problem with finite column boxes and row intervals, a multiplier chooses the row lower limit when positive and the upper limit when negative. A multiplier paired with an unbounded side is set to zero. Add this row contribution to the minimum of each component of the reduced cost over its original variable interval. This yields a lower bound for every LP point and hence for every admissible integer point. The multipliers need not be optimal, and numerical dispatches still need checking. This argument applies to the stored coefficient model. Meteorology, parameter uncertainty, forecasting and economic error are outside the certificate.

The HiGHS logs expose presolve status and MIP-start processing. LP-first escalation invokes a fresh unrestricted solver and does not reuse an LP basis. When an explicit LP precedes native search, the native call may redo overlapping relaxations. The logs cannot establish identity of its transformed root LP with the external LP. The no-fallback cases have no normalized fallback-to-bound area; every missing interval records its reason. Raw full-MIP results and native diagnostic numerical gaps are preserved even when an independent lower bound cannot reach the target.

## Post hoc exact primal reconstruction

All 20 small 4×8 cases entered the offline audit. The repeat-zero raw LP schedule failed the original physical screen on 8. The remaining 12 yielded recovered exact rational vertices of the original unrestricted coefficient model after fixing only the candidate device-hour modes. Every recorded box, inequality, equality and integer choice passed exact checking. The largest exact primal-minus-unrestricted-dual gap was 1.51e-13 cost units. Each one-MW mutation failed. This strengthens the small admissible-case result beyond tolerance-level primal replay. The offline proof time cannot be credited to the two-second campaign. See exact_primal_design.md and results/small_exact_primal.json.gz.
