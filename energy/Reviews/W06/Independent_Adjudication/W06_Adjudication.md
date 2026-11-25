# W06 — claim-by-claim adjudication

All 52 original claims; original v0.5 unchanged. ADMIT = within exact scope; NARROW = original claim retained with required qualification; HOLD = unresolved/not assertable affirmatively; REJECT = contradicted as stated. None of the carefully scoped original claims required outright rejection, but broader claims of generalized superiority, repeated-call reliability, and realized savings are not admitted.

ADMIT: 42 | NARROW: 9 | HOLD: 1 | REJECT: 0

## W06-B01 — ADMIT

**Original claim:** Minimization and maximization gaps admit pointwise and infimum/supremum ceilings, with strict/weak threshold distinction.

**Source evidence:** `B/formal/COA.lean#minInterval; B/formal/COA.lean#maxInterval`

**Independent review:** Inspected minInterval/maxInterval and derived lower/upper gap by subtracting common feasible incumbent; checked equality control U=10,L=9,J=9.

**Remaining obligation / scope:** Uniform bound and nonempty feasible set must be supplied in every application.

**Permitted v0.6 wording:** For a feasible incumbent and valid objective floor or ceiling, the optimality gap is bounded by the difference from that floor or ceiling. Strict exclusion of an inclusive target requires a strict bound unless nonattainment is proved.

## W06-B02 — ADMIT

**Original claim:** Nonattainment of the floor permits strict exclusion even where the ceiling equals the target.

**Source evidence:** `B/formal/COA.lean#strictAtNonattainment; B/formal/Tests.lean#nonattainment`

**Independent review:** Derived J(x)>L for every feasible x when L is not attained; therefore U-J(x)<U-L. Counterexample at attainment checked.

**Remaining obligation / scope:** Nonattainment must be established, not inferred from solver tolerance.

**Permitted v0.6 wording:** At a ceiling equal to the target, strict exclusion is valid only if no admissible candidate attains the relevant floor (or an equivalent strict bound is proved).

## W06-B03 — NARROW

**Original claim:** Finite weighted opportunity bounds admit missing-case fallback floors at original weights.

**Source evidence:** `B/formal/COA.lean#weightedPanel; B/formal/COA.lean#partialPanel`

**Independent review:** Summed individual inequalities with nonnegative weights; tested missing mass (0,4) at equal weights and negative-weight reversal. A retains two invalid paths.

**Remaining obligation / scope:** A missing baseline is not repaired by a fallback lower bound; need a valid baseline value and bound per weighted case; otherwise report incomplete coverage or separately justified enclosing baseline.

**Permitted v0.6 wording:** Finite weighted opportunity ceilings preserve original nonnegative weights. For a missing floor a valid fallback floor may be substituted without dropping weight, provided a valid baseline is available. Ineligible baselines remain explicitly unresolved; no full-panel mean certificate follows by omission.

## W06-B04 — ADMIT

**Original claim:** Relaxed/physical/observation-compatible/deadline-constrained infima are ordered; finer observations can be ignored.

**Source evidence:** `B/formal/COA.lean#operationalChain; B/formal/COA.lean#ignoreInformation`

**Independent review:** Inspected operationalChain and ignoreInformation, proved infimum order for inclusion and refinement of observation partitions. Reconstructed issued E decisions; actual future branch revealed only in planning approximation.

**Remaining obligation / scope:** Physical, adapted and deadline-feasible sets must truly nest under same objective; more information may incur compute or acquisition cost.

**Permitted v0.6 wording:** With a common objective and nested feasible domains, the relaxed, physical, observation-compatible and deadline-constrained infima are ordered. A policy can ignore extra observations only when refinement and the feasible-policy contract permit it.

## W06-B05 — ADMIT

**Original claim:** A cost floor excludes positive net value if gross ceiling is no greater; discounts preserve pointwise bounds.

**Source evidence:** `B/formal/COA.lean#netStop; B/formal/COA.lean#discountedNet`

**Independent review:** Subtracted implementation floor and multiplied by nonnegative discount weights; tested kWh/MWh scale error. Lean Amount tags encode same type, not real unit calibration.

**Remaining obligation / scope:** No justified implementation-cost floor or field net cash flows in W06; unit and horizon semantics require independent bridge.

**Permitted v0.6 wording:** A valid gross opportunity ceiling no greater than a justified implementation-cost floor excludes positive modeled net benefit. Nonnegative discounts preserve the bound if cash flows, units and horizons match.

## W06-B06 — ADMIT

**Original claim:** Boxed and mixed-row LP multipliers give exact lower certificates for feasible points.

**Source evidence:** `B/formal/BoxDual.lean#boxedDual; B/formal/BoxDual.lean#mixedRowDual`

**Independent review:** Independently rebuilt LP floors in A, rational UC and AC, including exact signed row-endpoint and box residual sums; wrong-sign control reproduced.

**Remaining obligation / scope:** One-sided rows need admissible multipliers; boxes must include original feasible set.

**Permitted v0.6 wording:** For a finite valid box and correctly signed row multipliers, the exact residual-and-endpoint expression is a lower bound; solver-reported dual feasibility is not necessary for this boxed certificate.

## W06-B07 — ADMIT

**Original claim:** Upper feasible gain and bounded transfer/enclosure require admissible candidates and explicit model maps or allowances.

**Source evidence:** `B/formal/COA.lean#feasibleGain; B/formal/COA.lean#transferBound; B/formal/COA.lean#enclosureCeiling`

**Independent review:** Derived transfer by composing feasible model map and one-sided objective inequality; verified AC rank-one lift and UC exact primal; checked infeasible incumbent/rounding counterexamples.

**Remaining obligation / scope:** Map, cost allowance, and actual feasibility must be demonstrated in each model.

**Permitted v0.6 wording:** A feasible improving candidate provides a lower bound on recoverable gain; transfer and enclosure require verified feasibility and explicit one-sided cost domination or allowance.

## W06-B08 — NARROW

**Original claim:** Conditional cost comparison preserves the imposed service, risk and stock contract. Uniform per-scenario loss bounds transfer to any monotone cash-shifting risk measure.

**Source evidence:** `B/formal/COA.lean#contractCost; B/formal/COA.lean#riskCeiling; B/formal/Tests.lean#meanTail`

**Independent review:** Derived pointwise J0(s)≤J(s)+e then monotonicity and cash translation; verified mean falls 50→40 while upper-half tail rises 50→80 in source control.

**Remaining obligation / scope:** Lean contractCost represents service/risk/stock by scalar functions; complete hourly service, multivariate risk, activation requirements and risk-functional premises must be verified separately.

**Permitted v0.6 wording:** A cost ceiling applies within the imposed service, risk and stock contract. A uniform per-scenario loss bound transfers to a monotone cash-translating risk functional with the required shift property; an average gain alone does not imply tail-risk improvement.

## W06-B09 — ADMIT

**Original claim:** Nonpositive expected penalties for every common policy turn augmented path floors into an aggregate lower bound.

**Source evidence:** `B/formal/COA.lean#infoPanelInf; B/formal/Tests.lean#infoExample; B/LITERATURE.md`

**Independent review:** Summed augmented floors and used nonpositive expected penalty for every admissible common policy; positive penalty=1 at true J=0 counterexample.

**Remaining obligation / scope:** No calibrated policy-wide martingale/centering certificate for operational E; do not infer it from one policy.

**Permitted v0.6 wording:** Information-relaxed path floors yield an operational aggregate floor only when penalty centering or a nonpositive expectation is proved for every admissible policy under the same weights and information pattern.

## W06-B10 — ADMIT

**Original claim:** A two-state common-action problem has perfect-foresight gap 1/2 and centered bound gap zero.

**Source evidence:** `B/formal/Tests.lean#independentActions; B/formal/Tests.lean#infoExample; B/results/exact_controls.json`

**Independent review:** Enumerated two shared actions with equal state weights; common optimum 1/2, PF optimum 0; centered bounds recover 1/2. Reran finite controls.

**Remaining obligation / scope:** Illustrative model only, not evidence for E policy gap.

**Permitted v0.6 wording:** The two-state toy problem exhibits a 1/2 perfect-foresight gap; a centered penalty closes that bound gap exactly under its shared-action contract.

## W06-B11 — ADMIT

**Original claim:** A continuous constant inventory credit telescopes and a uniform feasible closing repair of cost K caps the difference of the terminal-contract infima.

**Source evidence:** `B/formal/Closing.lean#telescope; B/formal/Closing.lean#terminalPremium; B/extension_plan.md`

**Independent review:** Telescoping cancellation by summation; derived infimum premium by uniform repair with cost ≤K; arbitrary replacement price disproves capacity-only dollar bound.

**Remaining obligation / scope:** Uniform closing repair not established for actual reserve/control applications; fixed credit alone is not total-cost premium.

**Permitted v0.6 wording:** Constant inventory marks telescope along a continuous path. A uniform feasible cross-contract repair costing at most K bounds the terminal-contract premium; capacity and inventory mark alone do not bound replacement costs generally.

## W06-B12 — NARROW

**Original claim:** The pinned build inspected 49 declarations, kernel-replayed four theorem modules and rejected eight designated invalid statements or type mismatches.

**Source evidence:** `B/results/lean/proof_audit.json; B/results/lean/Inventory.log; B/results/lean/FalseVariants.log`

**Independent review:** Read proof_audit.json, source, compile and kernel exit records and axiom inventory: 49 declarations, four successful kernel replays, eight designated invalid declarations rejected.

**Remaining obligation / scope:** No fresh Lean/mathlib compilation or clean kernel replay here; prebuilt imports, same kernel, statement/model correspondence separate.

**Permitted v0.6 wording:** The archived pinned Lean 4.30.0-rc2 build reports inspection of 49 declarations, successful replay of four theorem modules and rejection of eight designated false variants. This review inspected those records but did not independently rebuild Lean.

## W06-B13 — ADMIT

**Original claim:** Exact finite controls passed for 2250 LP witnesses, 12 domain-sign configurations and 1071 common-action and distribution pairs.

**Source evidence:** `B/exact_controls.py; B/results/exact_controls.json`

**Independent review:** Reran B/exact_controls.py; JSON identical including 2,250 LP witnesses, 12 sign cases, 1,071 common-action/distribution pairs. Independent rational certificate implementations also tested.

**Remaining obligation / scope:** Finite constructed controls do not prove general theorem or engineering applicability.

**Permitted v0.6 wording:** All 2,250 LP-witness tests, 12 sign configurations and 1,071 common-action/distribution tests reproduced on the declared rational grids.

## W06-B14 — ADMIT

**Original claim:** Under the flat W05 tariff and fixed hourly service, affine stock and cumulative discharge coefficients plus a valid ramp envelope bound economic gain.

**Source evidence:** `B/flat_review/FlatTariff.lean#tariffIdentity; B/flat_review/FlatTariff.lean#flatCap; B/flat_review/logs/audit.json`

**Independent review:** Independently derived affine energy-balance cost identity and bidirectional ramp envelope by min convolution; reconstructed exact physical paths, coefficients positive; inspected FlatTariff Lean records.

**Remaining obligation / scope:** Flat stationary tariff, efficiency, same hourly service, correct initial ramp/availability, nonnegative coefficients; no fresh Lean build.

**Permitted v0.6 wording:** Under the frozen flat-tariff storage model, fixed hourly service, and nonnegative stock/discharge coefficients, the bidirectional ramp envelope gives a lower bound on cumulative discharge and therefore on cost. The proof is conditional, not a general tariff theorem.

## W06-B15 — ADMIT

**Original claim:** Matched final stock leaves exactly zero flat-tariff cost opportunity for the archived feasible fill on 252 original cases and 12 retrospective splices.

**Source evidence:** `B/flat_review/data_check.json.gz; B/flat_review/check_data.py; E/historical/analytic_stock.json.gz`

**Independent review:** review_historical.py: exact reconstruction on 252 daily paths and 12 coupled splices; independently checked discharge equals envelope floor; 264 fresh min-discharge LPs found no improvement beyond roundoff.

**Remaining obligation / scope:** Historical synthetic reused panel, not general optimality of fill.

**Permitted v0.6 wording:** For every one of the 252 historical paths and 12 retrospective splices, the validated fill attains the unavoidable-discharge floor. Under identical hourly service, tariff, efficiencies, initial state and closing SOC, its modeled cost opportunity is exactly zero.

## W06-A01 — ADMIT

**Original claim:** Primary service threshold excluded 56 of 72 equal-weight paths and met by 14 feasible issued-schedule witnesses; two lack an admissible baseline.

**Source evidence:** `A/analysis/cases.csv; A/analysis/summary.json; A/results/shadow.json.gz`

**Independent review:** Independent forward DP + physical replay on 70 eligible service paths; exact thresholds and rational multiplier floors reproduced. 56 excluded,14 attainable,2 ineligible.

**Remaining obligation / scope:** Finite deterministic synthetic action lattice, four-hour comparator; no deployment frequency.

**Permitted v0.6 wording:** Of 72 prespecified service cases, 56 exclude the inclusive target, 14 meet it with a feasible witness, and two lack an admissible baseline.

## W06-A02 — ADMIT

**Original claim:** At the original hourly service profile, the cost target is excluded on 49/72 and met on 21; two baselines are ineligible.

**Source evidence:** `A/analysis/cases.csv; A/results/instances.json.gz; A/analysis/verification.json`

**Independent review:** Independent forward DP with fixed hourly service and stock contract, exact arithmetic: 49 exclusions,21 witnesses,2 invalid.

**Remaining obligation / scope:** Original modeled service vector, terminal rules and illustrative tariff only.

**Permitted v0.6 wording:** Under the unchanged hourly service and closing contract, 49 of 72 cost cases exclude the target, 21 meet it with a feasible witness, and two are ineligible.

## W06-A03 — ADMIT

**Original claim:** Power and energy rule out 37 service targets and 25 cost targets before LP. Exact LP adds three service and ten cost exclusions. Objective lattice adds zero.

**Source evidence:** `A/analysis/summary.json; A/analysis/cases.csv`

**Independent review:** Reconstructed cumulative tiers and exact strict inequalities; verified analytical floors against full independent finite optima, LP bound from original rows.

**Remaining obligation / scope:** Tier proportions panel-specific; later methods charged in timing, not assumed free.

**Permitted v0.6 wording:** Power/energy floors exclude 37 service and 25 cost cases; LP certificates add 3 and 10 respectively, lattice rounding adds none, and exact DP adds 16 and 14.

## W06-A04 — ADMIT

**Original claim:** All eight constructed optima match, including two equality controls; there are no false exclusions. Three deliberate invalidations were rejected.

**Source evidence:** `A/results/controls.json; A/analysis/verification.json; A/check.py`

**Independent review:** Independent forward enumeration matches eight controls including equality; reran shipped checker, all three invalidations rejected (SOC, wrong sign, missing row).

**Remaining obligation / scope:** Finite controls only; shipped mutation checker is a replay, not independent formal proof.

**Permitted v0.6 wording:** All eight constructed controls reproduced, including both inclusive-threshold equality cases. No false exclusions occurred on these controls; three designated invalidations were rejected.

## W06-A05 — ADMIT

**Original claim:** Native MILP actions attained the exact optimum on 140 eligible case-objectives and eight controls; native reported bounds coincided within 1e-6 native units.

**Source evidence:** `A/analysis/verification.json; A/analysis/bellman_check.json.gz; A/results/shadow.json.gz`

**Independent review:** Independent forward DP matched archived feasible native MILP costs for 140 case-objectives plus eight controls; native lower stats within 1e-6.

**Remaining obligation / scope:** Native reported bounds remain numerical; exactness is established by independent finite plant enumeration, not solver label.

**Permitted v0.6 wording:** Native MILP actions attain the independently enumerated exact optimum on all 140 eligible case-objectives and eight controls; reported numerical bounds agree within 1e-6 native units.

## W06-A06 — ADMIT

**Original claim:** Staged timed calls consumed more aggregate wall time than direct exact DP on both objectives and less than direct MILP.

**Source evidence:** `A/results/timed.json.gz; A/results/run.json; A/analysis/summary.json`

**Independent review:** Summed 216 warmed calls per arm/objective; all eligible/ineligible included, baseline construction validation and check counted; staged 1.63056/1.96214s vs DP1.47228/1.01652, MILP5.48164/3.04855.

**Remaining obligation / scope:** No fresh isolated-host timing replay; comparisons apply to archived run only, not industrial settings.

**Permitted v0.6 wording:** In the archived warmed benchmark, staging consumes more aggregate time than direct exact DP on both objectives and less than direct MILP. This does not establish a screening speedup against the strongest comparator.

## W06-A07 — NARROW

**Original claim:** All 1296 warmed decision calls returned within 0.5 s; each cold worker launch and public warm-up exceeded 0.5 s.

**Source evidence:** `A/results/timed.json.gz; A/results/run.json`

**Independent review:** Checked all 1,296 archived warmed clock records, including ineligible; inspected cold start/public warmup 1.016–1.297s.

**Remaining obligation / scope:** No newly measured deadlines, service uptime or real-time guarantee; cold costs and validation remain in deployment accounting.

**Permitted v0.6 wording:** All 1,296 recorded warmed calls were within 0.5 s on the test host; each recorded cold launch/warmup exceeded 0.5 s. This is an observed timing result, not a hard real-time guarantee.

## W06-A08 — ADMIT

**Original claim:** Flat ample and scarce families exclude both targets on all 12 cases per family; all 12 time-of-use cost cases have feasible material improvements.

**Source evidence:** `A/analysis/cases.csv; A/analysis/summary.json`

**Independent review:** Independent per-family counts: 12/12 both flat ample and scarce exclude both targets, 12/12 time-of-use costs have improving witness.

**Remaining obligation / scope:** Deliberately designed families, no field frequency.

**Permitted v0.6 wording:** Both flat-ample and scarce families exclude both targets on all 12 paths per family, while all 12 time-of-use cost paths provide a material feasible improvement, within the synthetic design.

## W06-A09 — ADMIT

**Original claim:** Post-primary eight-hour baseline raises exclusions to 67 and 61 of 72 for service and cost, respectively, with original targets and cost service profile fixed.

**Source evidence:** `A/exploratory/design.md; A/exploratory/results/cases.csv; A/exploratory/results/witnesses.json.gz`

**Independent review:** Replayed stronger baseline witnesses against independent full optimum and original thresholds; 67/72 service,61/72 cost.

**Remaining obligation / scope:** Post-primary reused cases, not confirmatory; unchanged original service profile required.

**Permitted v0.6 wording:** On the reused primary panel, an exploratory eight-hour baseline raises exclusions to 67/72 service and 61/72 cost under the original thresholds and cost service profile.

## W06-A10 — NARROW

**Original claim:** The LP bound is strictly below the exact discrete optimum on 32/70 service and 45/70 cost cells.

**Source evidence:** `A/results/shadow.json.gz; A/analysis/cases.csv; A/check.py`

**Independent review:** Compared exact rational LP certificate to independent discrete optimum: strictly below in 32/70 and45/70.

**Remaining obligation / scope:** Certificate can be loose; does not prove actual LP optimum has an integrality gap unless LP primal/dual equality is shown.

**Permitted v0.6 wording:** The evaluated rational LP lower certificate lies strictly below the exact discrete optimum in 32/70 service and 45/70 cost instances. These counts are certificate gaps, not necessarily exact LP integrality gaps.

## W06-E01 — ADMIT

**Original claim:** Recomputed 252 complete exact W05 fill witnesses and 504 rational diagnostic economic gaps.

**Source evidence:** `E/historical/results.json; E/historical/replay.py`

**Independent review:** Fresh E/historical/replay.py and nested prior review execution matched 252 exact fill schedules and all 504 rational diagnostic gap fractions; independent historical.py reconstruction.

**Remaining obligation / scope:** Retrospective re-execution, not fresh holdouts or operational evidence; prior-review algorithm replay distinguished from independent discharge proof.

**Permitted v0.6 wording:** All 252 archived exact W05 fill witnesses and 504 rational economic diagnostic gap fractions reproduced; the independent replay retains their original contracts.

## W06-E02 — ADMIT

**Original claim:** Exactly zero matched-service/stock cost opportunity in all 252 W05 cases and 12 coupled paths.

**Source evidence:** `E/historical/analytic_stock.json.gz; E/historical/analytic_stock.py; E/protocol/analytic_extension.md`

**Independent review:** Exact ramp-envelope saturation independently reconstructed, plus 264 fresh minimum-discharge LP checks.

**Remaining obligation / scope:** Historical flat-tariff fixed-stock and fixed-service paths only; no general fill theorem.

**Permitted v0.6 wording:** The fixed-hourly-service and fixed-closing-stock opportunity is exactly zero on all 252 historical W05 cases and 12 retrospective splices under the frozen tariff and battery model.

## W06-E03 — ADMIT

**Original claim:** At original W05 scale single horizon inventory ceiling at most $1,175.54 subject to discharge saturation; four 30-day splices each bound at $39.19/day (rounded up).

**Source evidence:** `E/historical/splice.json.gz; E/historical/splice_audit.json; E/historical/analytic_stock.json.gz`

**Independent review:** Derived k_s=13.829787234... USD/MWh. Four 30-day splices each close at180, floor95; k_s·85=1175.5319149, divide30=39.1843972; upward cent bounds.

**Remaining obligation / scope:** Stock ceiling conditional on discharge saturation and matched hourly service; attainable savings, subsequent obligations, variable tariffs unproved.

**Permitted v0.6 wording:** The frozen flat-price model bounds the single-horizon inventory opportunity by $1,175.54 and each of the four continuous 30-day retrospective splices by $39.19/site-day, upward rounded. These are ceilings, not realized savings.

## W06-E04 — ADMIT

**Original claim:** Against price rule, mean fresh perfect-foresight headroom $100.91/$83.18 per site-day at 7/30 days.

**Source evidence:** `E/results/gate.json; E/results/audit.json; E/inputs/; E/protocol/freeze.sha256`

**Independent review:** Independent finite Bellman potentials and exact optimal paths over same actual trajectory; price baseline 100.9143 and83.1825 dollars/day above perfect foresight.

**Remaining obligation / scope:** Information relaxation, finite lattice, fixed terminal9 and complete service; not attainable causal opportunity.

**Permitted v0.6 wording:** Against the price rule, mean perfect-foresight opportunity ceilings in the 7/30-day synthetic panels are $100.91/$83.18 per site-day under the declared finite plant and matched terminal and service contracts.

## W06-E05 — ADMIT

**Original claim:** Checked 8,260,320 finite-plant Bellman edges over 128 offline objectives and reconstructed attaining paths.

**Source evidence:** `E/audit.py; E/results/summary.json; E/results/cert_69103_7.json.gz`

**Independent review:** Independent Bellman graph reconstruction verified 8,260,320 edges, all128 primary offline objectives and attaining paths, matching potentials.

**Remaining obligation / scope:** Only declared finite state-action lattice and exogenous trajectory; physical continuous plant not covered.

**Permitted v0.6 wording:** The independent finite-graph replay verified 8,260,320 primary Bellman edges over 128 offline objectives and independently recovered attaining paths.

## W06-E06 — ADMIT

**Original claim:** Fresh flat-tariff optimal stock-only value $4.21/$0.67 per day, versus $28.43/$26.63 under artificial daily resets.

**Source evidence:** `E/results/summary.json; E/results/audit.json; E/gate.py`

**Independent review:** Independently reconstructed exact DP and daily reset sums: flat continuous4.2143/.6667 vs reset28.4286/26.625.

**Remaining obligation / scope:** Separate artificial reset estimand, same hourly service and $50 terminal mark, not recurring savings.

**Permitted v0.6 wording:** Under the fresh flat-tariff stock-only comparison, continuous 7/30-day effects average $4.21/$0.67 per day, versus $28.43/$26.63 under artificial daily resets.

## W06-E07 — ADMIT

**Original claim:** On continuous variable-price paths optimal stock-only effect averaged $25.39/$7.35 per day.

**Source evidence:** `E/results/summary.json; E/results/audit.json`

**Independent review:** Independent variable tariff Bellman optima match stock-only comparison:25.3893/7.35125.

**Remaining obligation / scope:** Offline perfect foresight, $50 closing mark, matched fill terminal vs floor; horizon boundary value, not field net benefit.

**Permitted v0.6 wording:** On the continuous variable-price paths, the modeled optimal stock-only effect averages $25.39/$7.35 per day for 7/30-day horizons under the frozen terminal credit and service/standby contract.

## W06-E08 — ADMIT

**Original claim:** H12 fitted terminal mark gains $55.32/$40.45 per day against the price rule and $46.96/$48.40 against H12 zero tail.

**Source evidence:** `E/results/paired_paths.csv; E/results/summary.json; E/results/continuation_fit.json`

**Independent review:** Recomputed every nominal action/cost and issued observations; gains55.3232/40.4496 vs price and46.9554/48.4025 vs zero-tail H12.

**Remaining obligation / scope:** Eight synthetic families; not strongest comparator and not calibrated net benefit; do not transfer to new tariff/wear.

**Permitted v0.6 wording:** The fitted H12 terminal mark improves the original price rule by $55.32/$40.45 per site-day and the H12 zero-tail comparator by $46.96/$48.40 on the paired synthetic 7/30-day paths; it loses on mean to the supplementary three-scenario policy.

## W06-E09 — NARROW

**Original claim:** All four sign tests on improvement exceeding $15/day have Holm-adjusted p=0.015625.

**Source evidence:** `E/protocol/design.md; E/results/summary.json; E/audit.py`

**Independent review:** Recomputed all eight per-seed effects exceed $15 in each of four contrasts; sign p=1/256, Holm adjusted4/256=0.015625.

**Remaining obligation / scope:** Conditional on independent seed-level sign-test null and pre-specified family; shared generators, paired horizons and post hoc policies do not provide external validation.

**Permitted v0.6 wording:** For the four preregistered contrasts against the original comparators, all eight seed-level gains exceed $15/day; conditional on the sign-test assumptions, Holm-adjusted p=0.015625. No inference is made against the stronger supplementary comparator or field population.

## W06-E10 — ADMIT

**Original claim:** The fitted mark loses to a stronger 3-scenario H12 comparator on mean ($2.03/$2.35 per day); no case beats it by $15.

**Source evidence:** `E/protocol/supplement.md; E/results/supplement_summary.json; E/supplement.py`

**Independent review:** Reconstructed actual forecast issues and 14,208 three-scenario actions across both contracts; costs independently replayed. Primary continuation loses2.0286/2.3458; no >15 win.

**Remaining obligation / scope:** Post-primary reused panel; optimistic two-stage branch-dependent future recourse inside causal rolling policy, not fully nonanticipative tree.

**Permitted v0.6 wording:** The supplementary three-scenario H12 comparator beats continuation on mean by $2.03/$2.35 per site-day, and no case gives continuation a $15/day advantage. This is a matched-information synthetic comparison.

## W06-E11 — NARROW

**Original claim:** Applied all jobs and protected service with verified headroom and final 9 MWh for each matched controller. Pending booked work crossed all 280 internal midnights.

**Source evidence:** `E/results/audit.json; E/results/supplement_summary.json; E/audit.py`

**Independent review:** Independent nominal replay checked physical action bounds, cost, booked service, final9 for matched arms and 280 pending-work internal midnights. Free-fill diagnostic deliberately has different terminal.

**Remaining obligation / scope:** Standby headroom not activated reserve; nominal modeled service only, no real SLA or queue validation beyond generator.

**Permitted v0.6 wording:** Matched primary and supplementary controllers deliver all declared booked/protected load, respect the modeled standby headroom, and finish at 9 MWh; pending booked work crosses all 280 internal midnights. The free-fill diagnostic is not a matched-stock controller.

## W06-E12 — ADMIT

**Original claim:** Optional-work valuation lowers modeled offline costs while losing 980/1253 and 4278/5558 low-priority jobs.

**Source evidence:** `E/results/audit.json; E/results/summary.json`

**Independent review:** Independent exact optional-drop DP and attaining path; 980/1253 and4278/5558 optional low-priority jobs missed.

**Remaining obligation / scope:** Separate shedding contract with $18 assumed job penalty; not service-preserving.

**Permitted v0.6 wording:** The separate offline optional-work valuation reduces modeled costs while omitting 980/1,253 and 4,278/5,558 low-priority jobs in the 7/30-day panels. It is not a matched-service gain.

## W06-E13 — NARROW

**Original claim:** 83 primary guard fallbacks occurred; zero measured one-second misses out of 42624 primary/diagnostic decisions.

**Source evidence:** `E/results/audit.json; E/results/summary.json`

**Independent review:** Recomputed primary 42,624 logged decisions, 83 guard fallbacks and checked no archived one-second misses; verified applied actions.

**Remaining obligation / scope:** Archived timing only; no independent fresh timing or actuation clock; includes free-fill diagnostic.

**Permitted v0.6 wording:** The archived run records 83 guard fallbacks and no measured one-second misses among 42,624 primary/diagnostic decisions. All saved applied actions checked; this is not a deployment deadline guarantee.

## W06-E14 — ADMIT

**Original claim:** All 24 explicit time-expanded HiGHS LP objectives matched exact rolling H12 and admitted applied actions.

**Source evidence:** `E/results/supplement_summary.json; E/supplement.py`

**Independent review:** 48 fresh scipy HiGHS LPs using independently reconstructed graph: 24 unrestricted and24 first-action-fixed; all objective values match archived exact DP.

**Remaining obligation / scope:** First 24 epochs of first 7-day path only; not whole stochastic controller proof.

**Permitted v0.6 wording:** On the prescribed 24 H12 no-tail windows, the independently constructed network-flow LP optimum agrees with exact DP and each archived first action belongs to an optimal path.

## W06-E15 — HOLD

**Original claim:** No field/net deployment benefit or calibrated multi-market reliability claim.

**Source evidence:** `E/protocol/design.md; E/FINDINGS.md`

**Independent review:** Inspected synthetic protocol, compared contract effects, found stronger comparator negative and repeated-call counterexample.

**Remaining obligation / scope:** Field trace, actual reserve activations, realistic wear, workload penalties, implementation costs and reliability calibration absent.

**Permitted v0.6 wording:** No field benefit, positive deployment net value, accredited capacity, or calibrated multi-market reliability conclusion is established by W06.

## W06-E16 — ADMIT

**Original claim:** All 16 repeated holdouts admit nominal complete service, mandatory one-hour call deliverability and no-further-call terminal recovery under the stronger contract.

**Source evidence:** `E/reserve_activation_followup/results/gates.json; E/reserve_activation_followup/results/audit.json`

**Independent review:** Independent one-call Boolean viability and no-further-call recovery kernels agree, all16 nominal paths and offline attaining costs checked; tested physical activation endpoints.

**Remaining obligation / scope:** Post hoc reused panel; one call at a time, arbitrary subsequent availability envelope plus public clear window; block-based not equal AC MW.

**Permitted v0.6 wording:** All 16 reused paths admit complete nominal service and mandatory single-hour-call deliverability followed by a feasible no-further-call terminal recovery within the strengthened internal-block contract.

## W06-E17 — ADMIT

**Original claim:** Each policy passed all 1655 up and 1629 down calls; continuation supported 4781 stacked optional calls.

**Source evidence:** `E/reserve_activation_followup/check.py; E/reserve_activation_followup/results/audit.json`

**Independent review:** Independent one-call replay: each policy 1,655 up/1,629 down; continuation 4,781 stacked optional calls. Constructed consecutive-down failure seed69103_7 hour4, S9→11→12 with ramp constraints; additional two-call viability kernel.

**Remaining obligation / scope:** No repeated or actually deployed call guarantee; reserve cost after activation untested.

**Permitted v0.6 wording:** Each policy passes all 1,655 individual upward and 1,629 downward perturbations, and continuation passes 4,781 stacked optional tests. The tests are independent single-call perturbations; a consecutive-call counterexample prevents extending the claim to repeated activation.

## W06-E18 — ADMIT

**Original claim:** On hardened standby, continuation beats price by $72.25/$61.12 per day but gains only +$0.14/−$2.78 against stochastic at 7/30 days; 0/16 meet $15 versus stochastic.

**Source evidence:** `E/reserve_activation_followup/results/audit.json; E/reserve_activation_followup/protocol.md`

**Independent review:** Independent hardened nominal costs:72.2482/61.1217 vs price, +.14464/-2.7804 vs scenario; all16 paired effects <=15.

**Remaining obligation / scope:** Post hoc repeated-panel no-call costs; actual activated costs and external paths unresolved.

**Permitted v0.6 wording:** In the hardened standby model, continuation gains $72.25/$61.12 per day against the price rule and +$0.14/−$2.78 against three-scenario control on 7/30-day paths; none of 16 comparisons against three-scenario exceeds $15/day.

## W06-C01 — ADMIT

**Original claim:** All 12 full AC candidates admit certified nearby exact feasible points in the six benchmark snapshots

**Source evidence:** `C/ac_results/; C/ac_witness.py; C/independent_review/receipt.json`

**Independent review:** New mpmath interval reconstruction at 65 decimal digits; exact rational residual/norm sums from rounded inverse; all12 contractions verified, physical transformer currents both ends, generator/voltage/angle boxes.

**Remaining obligation / scope:** Static model, fixed reference and selected variables; interval library trust remains; no fresh local AC optimization or SCOPF.

**Permitted v0.6 wording:** All 12 archived AC candidates admit nearby exact feasible points in the six encoded static benchmark snapshots; a separate interval implementation verifies contraction and physical limits.

## W06-C02 — ADMIT

**Original claim:** Three of six primary AC cases exclude a one-percent cost reduction versus the selected local witness

**Source evidence:** `C/ac_results/; C/ac_bound.py`

**Independent review:** Independent decimal MATPOWER decode and outward rational flow row envelopes, convex fuel/thermal/voltage-product cuts and all multiplier certificates. All three typical case exclusions reproduced.

**Remaining obligation / scope:** Threshold relative to selected feasible upper enclosure; static AC no contingency or dynamic claims.

**Permitted v0.6 wording:** Three of six primary static AC cases exclude a cost reduction of at least 1% from the selected validated feasible reference; the exact lower certificates and interval upper bounds were independently reconstructed.

## W06-C03 — ADMIT

**Original claim:** All three stressed cases remained open after the primary cut budget

**Source evidence:** `C/ac_results/; C/freeze.json`

**Independent review:** All three stressed primary gaps independently checked:44.6814%,1.4179%,12.5079%.

**Remaining obligation / scope:** Open gaps are upper bounds on possible improvement, not feasible savings.

**Permitted v0.6 wording:** All three stressed cases remain open at the preregistered 1% target after the primary cut budget. No savings inference follows from an open bound gap.

## W06-C04 — ADMIT

**Original claim:** Certified clique cuts on reused stressed cases close the 39-bus case and narrow the 30- and 89-bus intervals

**Source evidence:** `C/exploratory/results/; C/clique.py`

**Independent review:** Independent clique fill, angle tan rounding outward and PSD cut algebra; evaluated every round dual with exact rational arithmetic. New gaps4.1027%,0.6878%,11.9093%.

**Remaining obligation / scope:** Exploratory reused cases, not added to primary denominator or speed comparison.

**Permitted v0.6 wording:** In the separate exploratory stressed-case replay, clique cuts exclude the 1% target for 39 buses and narrow the ceilings for 30 and 89 buses; primary results remain 3/6.

## W06-C05 — ADMIT

**Original claim:** Three of four full-UC cases exclude a one-percent target against a rationally feasible incumbent

**Source evidence:** `C/uc_results/; C/independent_review/receipt.json`

**Independent review:** Independent direct rational reconstruction from original UC decimals, 55,338 rows, canonical labels, primal feasibility, binary and branch certificates. Gaps .25248,1.69889,.72720,.34738%.

**Remaining obligation / scope:** PGLib-UC systemwide balance/reserve only, not SCUC. No new native solver run.

**Permitted v0.6 wording:** Three of four primary full-UC instances exclude a 1% cost reduction relative to exact-rational feasible incumbents under the published UC formulation and exact-decimal inputs.

## W06-C06 — ADMIT

**Original claim:** Two native MILP runs reach their solver time limit; one still has a checked exclusion

**Source evidence:** `C/uc_results/`

**Independent review:** Inspected native MILP status in canonical summary; two time limit cases, Sep20 8h remains excluded with exact independently checked bound.

**Remaining obligation / scope:** Archived single-thread 30s solver limit, not fresh runtime or end-to-end deadline.

**Permitted v0.6 wording:** Two archived UC native MILP calls report the solver time limit; one nonetheless has a valid independently reconstructed 1% exclusion.

## W06-C07 — ADMIT

**Original claim:** The 31-node rational disjunction still leaves the February 24-hour case open

**Source evidence:** `C/exploratory/uc_results/; C/uc_tree.py`

**Independent review:** Independently rebuilt all31 rational node lower bounds and verified 16 leaves form exhaustive binary branch coverage. Final ceiling1.63357828%.

**Remaining obligation / scope:** Reused Feb24h case, not savings; no improving feasible witness at target supplied.

**Permitted v0.6 wording:** The exploratory 31-node, 16-leaf exhaustive rational disjunction narrows the February 24-hour ceiling to 1.63358%, leaving the 1% opportunity unresolved.

## W06-C08 — NARROW

**Original claim:** Independent arithmetic checks exposed rounded RHS and non-replayable solver ordering in intermediate UC attempts

**Source evidence:** `C/diagnostics/; C/independent_review/README.md`

**Independent review:** Read intermediate logs and checked old unlabeled primal/dual vectors in canonical ordering; row/box errors and invalid signs expose non-replayability; canonical exact decimals independently replay.

**Remaining obligation / scope:** No fresh reproduction of historical solver ordering or isolated attribution of old errors to RHS alone; logs document float-RHS correction.

**Permitted v0.6 wording:** The archive records rounded-RHS and ordering issues in intermediate UC attempts. Old unlabeled vectors fail canonical replay; only the reissued canonical exact-decimal artifacts pass independent checks and are admitted.

## W06-E19 — ADMIT

**Original claim:** Across 160 fixed schedules, at $150/kWh the continuation policy loses to three-scenario by $7.32/$3.90 per site-day under primary and $3.07/$2.54 under one-call (7/30 days). One-call seven-day sign flips near $59.16/kWh.

**Source evidence:** `E/wear_sensitivity/results.json; E/wear_sensitivity/revalue.py; E/wear_sensitivity/README.md`

**Independent review:** Reran shipped rainflow revalue.py, output JSON identical all160; checked two independent histogram routines in script, whole-path accounting and E nominal cost reconstruction.

**Remaining obligation / scope:** Fixed schedules only, illustrative depth curve/cell replacement costs; reoptimization, calibration and activated wear unresolved.

**Permitted v0.6 wording:** At $150/kWh, frozen-schedule rainflow revaluation puts continuation behind three-scenario control by $7.32/$3.90 per site-day under primary standby and $3.07/$2.54 under one-call standby (7/30 days); the one-call 7-day sign flips near $59.16/kWh. This is not a reoptimized or calibrated battery-life result.

