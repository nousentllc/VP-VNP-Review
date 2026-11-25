# Battery grouping under a dispatch deadline

**CRGC W03 experimental results · 24 November 2026 · Private research handoff**

## Decision for the whitepaper

Grouping heterogeneous batteries sometimes produced a better dispatch sooner than the full mixed-integer solver. On five of six deliberately difficult instances it improved the common fallback sooner, comparing the median of three trials per case. **No grouped stage reached the prespecified cost gap.** The adaptive policy reached it on 20 of 24 held-out cases, the same 20 as the full mixed-integer program (MILP). The full linear program (LP) alone reached it on 18. On those 18 cases, the adaptive method accepted the LP solution before forming a group.

The defensible empirical claim concerns **time to a first improvement on this stress panel**. A solver-speedup claim at matched quality would require an advantage over both the full MILP and the validated LP or its recovery policy. This campaign did not establish that advantage. Keep a grouped incumbent and a full-model lower bound as distinct quantities in the manuscript.

| Register item | What ran | Disposition |
|---|---|---|
| W03-A · Battery grouping | 24 held-out instances, 450 timed policy trials | LP passed on 18 cases. Six adversarial cases required independent device modes. |
| W03-B · Formal verification | Lean build, axiom inspection, exact controls | The balanced lift, its endpoint condition and the unequal-efficiency obstruction have machine-checked statements. |
| W03-C · AC power flow | Three formulations on six public network cases, twice each | All 36 dispatches passed AC checks. Elimination preserved cost to numerical tolerance. Timing gains varied by case. |
| W03-D · Unit commitment | Two fleets, two horizons, two formulations | Pairing increased feasible cost on all three comparable cases. The fourth produced no incumbent in either arm. |
| W03-E · Computing load and storage | Historical replay and 24 paired synthetic operating days | The forecast rule served more load on 20 days and tied on four. The tested rolling optimizer won on zero. |

The research branch records the design before held-out evaluation, followed by the input hashes and the development-selected battery settings. Reported timings come from a single eight-logical-CPU ARM64 Mac with each solver limited to one thread. The benchmark data are public or synthetic. No operating utility, commercial site or production battery participated. [Frozen experimental design](https://github.com/nousentllc/VP-VNP-Review/commit/327b1109fbca2e53958818a3ac884e11e6aee724) · [Battery input and code freeze](https://github.com/nousentllc/VP-VNP-Review/commit/4a2f36919877503b60d093cba22bef1a4a1cfe0b)

**Fresh replay.** A second end-to-end run on the same machine reproduced all 450 battery target decisions and the same five earlier first improvements. Its proof checks, AC costs and forecast-policy service and loss totals matched. The UC run reproduced all eight deadline classifications. Several UC incumbents changed within the solver gap or time limit. Both runs’ raw outputs are included. [Run-to-run comparison](results/reproduction.json)

## W03-A · Where grouping helped and failed

Each one-hour model minimizes import expenditure plus linear battery throughput cost. Every device has its own charging and discharging efficiency, available power, state-of-charge (SOC) limits, terminal condition and direction of operation. Grid import obeys balance, limits and a ramp from the previous hour. Sharing a mode ties a binary decision across members. Each member retains its own power and SOC. Fixed proportional control also fixes member powers in proportion to capacity.

With import price λ, throughput coefficient k and AC-side powers c and d, the objective and individual energy balance are

$$\min \sum_t \left(\lambda_t g_t+\sum_i k_i(c_{it}+d_{it})\right),\qquad e_{i,t+1}=e_{it}+\eta_{ci}c_{it}-d_{it}/\eta_{di}.$$

Two held-out seeds at each of three sizes gave six cases per cohort. The sizes were four devices over eight hours, eight over 12 and 12 over 16. Ordinary cases have unequal parameters and initial SOC. The second cohort adds negative prices, outages and reserve floors. The interchangeable cohort permits exact permutations of complete device mode histories. The forced cohort requires positive import in every hour, zero site load and restoration of each device’s initial SOC. A feasible alternating device schedule is supplied to all methods. An all-idle schedule violates import in that cohort. The synthetic cases were designed to expose mechanisms. Their frequencies cannot estimate how often the mechanisms occur in a grid.

**Primary endpoint.** The two-second clock includes fallback validation, model construction, presolve, solve, reconstruction and validation. A target hit requires a feasible cost U and unrestricted lower bound L satisfying U − L ≤ 0.00002 + 0.001 × max(1, |U|). The absolute term handles small costs. Every trial starts with the same checked fallback. The solver receives its power values as a partial MIP start when compatible. The full MILP presolve setting was selected on eight separate development cases. Both settings reached all eight targets and presolve on had the lower median time.

| Cohort · six cases each | Raw LP targets | Full MILP targets | Adaptive targets | Median capped ms, LP / MILP / adaptive |
|---|---:|---:|---:|---:|
| Ordinary heterogeneous | 6 | 6 | 6 | 3.19 / 40.44 / 3.16 |
| Negative prices and outages | 6 | 6 | 6 | 2.95 / 20.20 / 2.86 |
| Interchangeable | 6 | 6 | 6 | 3.32 / 26.85 / 3.35 |
| Forced opposing modes | 0 | 2 | 2 | 2,000 / 2,000 / 2,000 |

A case hit here means all three repeats hit. For timing, each miss takes the full two seconds. The table takes the median within case, then across cases. On the forced cohort, a median of two seconds reflects four censored cases. It does not assign a solve time to them. Six cases per cohort and three timing repeats support descriptive comparisons. The paired intervals and individual differences are in the packet. [Cohort results](results/A/cohorts.csv) · [Paired timing differences](results/A/paired.json)

**Why the methods diverged.** The adaptive policy first checks the full LP solution, then tries one shared mode when necessary. It splits groups using differences in LP net power and ultimately restores independent modes. All six forced cases returned an LP optimum that charged and discharged at least one battery simultaneously. The root group was infeasible in all six. Subsequent groups produced feasible improvements. The first such improvement typically came sooner than with the full MILP, but its cost could be materially higher. The full model supplied the adaptive policy’s final winning schedule on all six. The two 4-device cases reached the target. Neither the 8-device nor the 12-device forced cases reached it in either arm. LP sign repair followed by full recovery also reached exactly those two. The raw LP arm retained the common fallback on all six.

| Forced case · devices × hours, seed | First improvement, full MILP (ms) | First improvement, adaptive (ms) |
|---|---:|---:|
| 4 × 8, 7301 | 48.47 | 101.13 |
| 4 × 8, 8297 | 104.68 | 23.23 |
| 8 × 12, 7301 | 332.72 | 161.69 |
| 8 × 12, 8297 | 317.72 | 44.25 |
| 12 × 16, 7301 | 888.67 | 276.78 |
| 12 × 16, 8297 | 1,134.42 | 43.39 |

Times in this secondary comparison stop at the first independently checked cost strictly below the common fallback. The two policies can therefore reach this endpoint at different costs. This distinction matters to a dispatcher who needs a particular quality by a deadline.

In ordinary heterogeneous cases, the fixed two-group mode restriction missed the full solver’s cost in two of six first-repeat returns. Fixed proportional control cost more in all 12 ordinary and negative-price cases. In the forced cohort, four of six two-group proportional models were infeasible. The four are failures of the restriction even though the full problem has a constructive feasible schedule. On interchangeable devices, lexicographic symmetry breaking reached every target but took a median 74.75 ms versus 26.85 ms for the full MILP. As an inner restriction, a grouped model supplies an upper bound after successful lifting. Its own dual bound cannot certify unrestricted quality.

**Audit.** First-repeat powers were preserved for every returned candidate and best schedule. A separately written device-by-device replay checked 367 schedules and agreed with every admissibility classification. The largest residual on an accepted solver return was below 3.2 × 10⁻¹² in the checked units. For each full LP, an exact rational evaluation of its box Lagrangian reconstructed a lower bound for the stored binary64 coefficients. The largest difference from the reported LP objective was below 1.9 × 10⁻¹² cost units. MILP dual bounds remain solver-reported numerical bounds. Standalone presolve measurements cover 120 case/formulation combinations. They are diagnostics outside the timed trials. [Stage-level outcomes](results/A/stages_first_repeat.csv) · [Exact lower bounds and dual witnesses](results/A/exact_lp_certificates.json)

## W03-B · What the formal proof covers

The Lean file defines a full labeled trajectory, its total-energy projection, an aggregate trajectory and its balanced reconstruction. For N positive, divide total S into N integer parts with the first S mod N members one unit above the quotient. This is the manuscript’s lift with the device order reversed once for the entire trajectory. Capacity and rate are integers. For identical, ideal devices, a step of at most N times the individual rate lifts within every member’s rate. Along a monotone total-energy step, total absolute device movement equals the absolute aggregate movement.

Both endpoints use the same labeling. With any constraint and fee that depend only on the aggregate path, and any nonnegative real linear cycling price, the full and aggregate formulations attain exactly the same cost thresholds. This also covers an empty feasible set. Prescribed labeled endpoints (1,0) and (0,1) illustrate the necessity of the endpoint condition. Both have total one. Their aggregate motion costs zero, while swapping them costs two units of movement.

For nonideal devices, the proof sums the actual per-period SOC equation. Two positive-weight members with different round-trip efficiencies and fixed proportional charge and discharge must have zero common throughput when each ends at its initial SOC. Under terminal tolerances, the proof bounds the product of total common charge and the absolute efficiency difference by the sum of each tolerance scaled by discharge efficiency divided by member weight. The bound is necessary. A rational example in the packet attains it with nonzero charge.

Write C and D for common charging and discharging power, w for the allocation weights and δ for terminal energy tolerances. The cyclic identity for member i and the two-device tolerance inequality are

$$\sum_t D_t=\rho_i\sum_t C_t,\quad \rho_i=\eta_{ci}\eta_{di},\qquad |\rho_i-\rho_j|\sum_t C_t\leq \frac{\eta_{di}\delta_i}{w_i}+\frac{\eta_{dj}\delta_j}{w_j}.$$

Lean 4.30.0-rc2 compiled the statements against a pinned mathlib revision. The log lists the axioms of 16 declarations, including both end-to-end storage theorems. It contains the standard logical axioms propext, Classical.choice and Quot.sound as applicable. There are no admitted proofs in the source or sorryAx dependencies in the recorded build. Four false concrete claims failed compilation, four corrupted toy primal/dual certificates were rejected, and 27,776 finite balanced-lift transitions passed an independent integer check. The proof does not verify the optimizer implementation, the floating-point dispatches, the economics or VP/VNP. [Proof source](formal/Storage.lean) · [Compiler output](results/B/lean-build.log) · [Mutation and arithmetic results](results/B/checks.json)

## W03-C · Exact elimination in AC power flow

At a generator bus, solve the two local AC balance equations for one generator’s active and reactive output. Put its original limits directly on the reconstructed outputs and retain its cost. The remaining voltage and generation variables obey the same branch-end thermal limits, angle limits, shunts and transformer relations. This substitution reduces decision variables and preserves the static model wherever the selected generator’s P and Q enter balance with unit coefficients. It uses the local equations directly. The VP/VNP result supplied no algorithmic step.

The full sparse IPOPT baseline used exact automatic derivatives. We compared a flat start, a DC-based start, and elimination with the same DC start for the retained variables. Both formulations used the solver setting selected on the three-bus development case. The full and reduced starts can imply different initial generator outputs because the reduced formulation reconstructs them from voltages. The comparison includes that practical consequence. Every run had the same 12-second limit. All 36 finished within it. The downloaded normal and active-power-increase cases span 5, 14 and 30 buses.

| Case | Full / reduced variables | Feasible cost, normal / stressed ($/h) | Reduced minus DC-start full, normal / stressed (ms) |
|---|---:|---:|---:|
| 5-bus PJM | 20 / 12 | 17,551.89 / 78,949.91 | +0.92 / +0.28 |
| 14-bus IEEE | 38 / 28 | 2,178.08 / 5,999.36 | −0.66 / +0.42 |
| 30-bus IEEE | 72 / 60 | 8,208.52 / 18,036.59 | −0.23 / −1.12 |

All costs agree with the archive’s independently published AC baseline at its displayed precision. Across formulations within a case, the largest difference in median cost was below $0.000002/h. Branch-current reconstruction checked both ends, power balance, generator and voltage boxes and angle bounds. All 36 deliberately corrupted generation vectors failed. Separately computed lossless economic-dispatch support bounds are valid numerical lower estimates for these nonnegative-loss cases. The residual gap and the use of a local nonlinear solver leave global optimality open. Two repeats per formulation gave mixed timing signs. This experiment covers static AC-OPF. [Case results](results/C/comparison.csv) · [Published PGLib baseline](https://github.com/power-grid-lib/pglib-opf/blob/dc6be4b2f85ca0e776952ec22cbd4c22396ea5a3/BASELINE.md)

## W03-D · The cost of tying generator commitments

The baseline runs the published PGLib-UC mixed-integer formulation, retaining initial histories, minimum up/down times, output and reserve, ramps, startup categories, piecewise costs and renewable availability. The restriction pairs similar units within matching initial on/off, minimum-time and must-run categories. It ties their on/off decisions and retains every individual physical constraint. This produced 33 pairs in the 73-thermal-unit RTS fleet and 304 in the 610-unit California fleet. The 12-hour prefixes inherit original initial histories and omit later obligations. The 48-hour cases use the supplied full horizon.

| Fleet and horizon | Full feasible cost | Paired feasible cost | Deadline outcome |
|---|---:|---:|---|
| RTS, 12 hours | 228,050.56 | 230,790.61 | Both passed within the 0.5% solver gap setting |
| RTS, 48 hours | 2,516,915.98 | 2,532,321.68 | Two validated incumbents at solver time limit |
| California, 12 hours | 9,322.20 | 9,441.22 | Both passed within the 0.5% solver gap setting |
| California, 48 hours | No incumbent | No incumbent | Both failed the 45-second end-to-end gate |

The paired model’s own lower bound exceeded the full model’s feasible incumbent on both 12-hour cases. With the solver-reported bounds, tying units cost **at least 1,683.71 benchmark cost units on RTS and 118.47 on California**, rounding down to cents. This comparison uses the paired lower bound to bound the cost of the restriction. On RTS at 48 hours the two bounds overlap, so only a difference between returned schedules is measured. The costs belong to separate benchmark instances and should not be added.

The nominal 45-second budget reserves 20% for reconstructing and checking the schedule. In the large California reference arm, the solver returned after 56.19 seconds. No validated action was available at the deadline. The paired arm also failed to return an incumbent. Both timeouts remain in the denominator. A feasible fallback was unavailable for that case. Six archived schedules passed a fresh reconstruction against every published model constraint plus an independently written chronological check. The 48-hour California cases used 305,664 declared variables each. The register’s unit-commitment experiment has no transmission or contingency equations. [Unit-commitment results](results/D/comparison.csv) · [Pinned reference model](https://github.com/power-grid-lib/pglib-uc/blob/39a7f38cf4703de92f0291f0c873c2e98c789301/uc_model.py)

## W03-E · A forecast rule beat the rolling optimizer on service

The historical W-E05 replay reproduced all 12 profile/policy combinations. In the flat, four-hour peak, eight-hour peak and alternating profiles, the earlier forecast-aware rule and LP again left 0, 8, 168 and 0 MWh unserved, respectively. That comparison used the full constructed load profile. The new trial records the forecast actually issued each hour.

Eight synthetic underlying days were each tested with ordinary forecasts, with battery outages and committed headroom, and with biased forecasts. The two online policies see the same current load, six-hour issued forecasts and one-hour outage notice. Both face a 100 MW import cap, a 23 MW/h ramp and a 35 MW / 180 MWh battery. The day ends at a minimum 95 MWh SOC, enforced with a common late-day reserve floor. Facility demand is fixed at 24 MW. Remaining demand represents computing power that can go unserved. Useful compute is served electrical MWh. Mapping it to jobs, service-level commitments or revenue would require workload measurements.

The forecast rule keeps a 95 MWh target and precharges for forecast deficits. The rolling optimizer first minimizes forecast unserved load in its six-hour horizon and then minimizes throughput at that service level. It has the same physical reserve floors and no extra value assigned to stored energy beyond its horizon. The offline 24-hour comparator sees realized loads and outages.

| Regime · eight paired days | Rule unserved MWh | Rolling optimizer unserved MWh | Perfect-foresight unserved MWh | Rolling wins / ties / losses |
|---|---:|---:|---:|---:|
| Ordinary | 422.95 | 471.26 | 212.37 | 0 / 1 / 7 |
| Biased forecast | 479.93 | 545.33 | 212.37 | 0 / 0 / 8 |
| Outage and reserve | 628.76 | 693.01 | 575.57 | 0 / 3 / 5 |

Across the paired scenario-days the rule served 177.97 more MWh. The rolling policy also incurred less throughput and conversion loss in every regime total. Lower cycling and better service lead to different rankings here. All individual actions passed replay, and neither online policy needed its fallback. In the outage regime the offline and online arms each lost 128 MW-hours of committed headroom availability over eight days. Holding SOC above its floor did not restore unavailable inverter power.

A plausible explanation is the rule’s precautionary energy target and the short optimizer horizon. The present comparison changes both features together. A predeclared terminal-value or horizon ablation on new days would test the attribution. Eight reused synthetic day seeds do not establish a site-level effect or distinguish battery wear from throughput. [Policy and service results](results/E/comparison.csv) · [Paired day differences](results/E/paired.json) · [Forecast code and input freeze](https://github.com/nousentllc/VP-VNP-Review/commit/30eb36e66821653e963ec106c5d6a00235ce584c)

## Integration limits

Retain the storage proofs with their endpoint, efficiency and coupling hypotheses. Treat the earlier grouped incumbent as a candidate for a follow-up test against an LP-informed full-MILP warm start under the same deadline. Failure to beat that comparator at matched quality would remove the remaining operational case for grouping on this panel. The rolling controller result applies to the implemented objective and terminal policy. Independent reproduction on a second machine, larger AC networks, many UC dates, operational forecast vintages, online field testing, accredited capacity and independently attributed dollar savings remain open. [Claim and evidence ledger](claims.csv) · [Reproduction instructions](README.md)
