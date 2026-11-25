# W04-E · Continuation value and prediction horizon

The six-hour continuation controller changed flexible unserved energy by **-11.430 MWh/day, descriptive 95% interval [-15.899, -7.175]** against the same deterministic six-hour controller without continuation. Against the strong matched-horizon rule its difference was **-5.034 MWh/day, descriptive 95% interval [-8.208, -1.972]**. A negative difference favors the continuation controller. At fixed H6 the continuation-versus-none gate **passed**. The preregistered service-benefit gate against the rule **passed** on this synthetic panel.

## Panel, information and estimands

Twenty-four new latent 24-hour days each appear under ordinary, biased-forecast and outage/reserve conditions. Each issue supplies a shared twelve-hour maximum forecast. A shorter policy sees only its prefix. The current observation and next-hour explicit outage disclosure are common. In the generator, the reserve schedule starts two hours before the workload peak starts, and the outage starts one hour after that peak starts. The public reserve calendar and the load forecast can therefore indirectly signal the event window beyond one hour. All matched arms receive the same schedule. The physical site has a 100 MW import cap, 23 MW/h ramp, 35 MW / 180 MWh battery, and a protected 24 MW noncurtailable facility load. The original reserve and terminal floors apply to every policy. Charge/discharge efficiencies are 0.94/0.93, opening inventory is 95 MWh and the closing minimum is 95 MWh. When an outage prevents the scheduled reserve from being supplied, dispatch power falls to zero and the unavailable obligation is counted separately. The offline benchmark sees actual future load and availability.

The twelve arms include three matching forecast rules, six deterministic horizon/terminal factorial controllers, the legacy W03 six-hour optimizer, one six-hour-information/twelve-hour-model diagnostic, and one offline reference. Each online arm applied its own observed state to the same prevalidated fallback rule. An individual action had a one-second wall gate. All comparisons are matched by day and regime. The primary mean first averages the three regime differences within each day. Intervals resample 24 whole days 10,000 times. All secondary intervals are descriptive and unadjusted.

## Service and resource tradeoffs

| Regime | H6 policy | Unserved MWh, 24 days | Conversion loss MWh | Battery throughput MWh | P95 decision ms |
|---|---|---:|---:|---:|---:|
| base | rule6 | 986.90 | 284.90 | 4,244.49 | 0.20 |
| base | none6 | 1,161.54 | 263.10 | 3,919.68 | 66.80 |
| base | value6 | 798.07 | 314.44 | 4,684.68 | 108.52 |
| base | offline | 398.70 | 366.48 | 5,459.93 | offline |
| biased_forecast | rule6 | 1,325.22 | 236.21 | 3,519.17 | 0.15 |
| biased_forecast | none6 | 1,434.09 | 223.95 | 3,336.45 | 261.55 |
| biased_forecast | value6 | 1,140.16 | 266.25 | 3,966.62 | 192.54 |
| biased_forecast | offline | 398.70 | 366.48 | 5,459.93 | offline |
| outage_reserve | rule6 | 1,544.00 | 208.00 | 3,108.27 | 0.30 |
| outage_reserve | none6 | 1,721.00 | 180.39 | 2,692.82 | 281.28 |
| outage_reserve | value6 | 1,555.45 | 207.19 | 3,098.16 | 260.80 |
| outage_reserve | offline | 1,433.19 | 217.61 | 3,242.08 | offline |

H6 continuation minus the matched rule by regime, in MWh/day with day-bootstrap intervals: base -7.868 [-12.287, -3.673], biased_forecast -7.711 [-12.914, -2.632], outage_reserve +0.477 [-0.309, +1.365]. The outage/reserve interval includes zero. At H12 the matched rule served more load than the continuation controller on average.

The offline rows report a full-day physical comparison. Their solve time is recorded separately. Loss and throughput are physical quantities. No degradation price or useful-job conversion was supplied. The controller rankings depend on which outcome is valued. The complete regime table also reports served load, import peak, terminal SOC and unavailable reserve headroom.

Across the 72 H6 comparisons against the rule, the continuation policy was weakly better in all three of unserved energy, conversion loss and throughput and strictly better in at least one on 4 cases. The rule dominated on 10, 20 tied in all three, and 38 had opposing changes. The tolerance for each quantity was 0.000001 MWh. These are descriptive scenario counts. The regimes within a day are dependent.

| Comparison, first minus second | Mean unserved MWh/day | Day interval | Days lower / tied / higher | Mean conversion loss Δ MWh/day | Mean throughput Δ MWh/day |
|---|---:|---:|---:|---:|---:|
| value6 − none6 | -11.430 | [-15.899, -7.175] | 23 / 1 / 0 | +1.673 | +25.007 |
| value6 − rule6 | -5.034 | [-8.208, -1.972] | 13 / 2 / 9 | +0.816 | +12.188 |
| none6 − legacy6 | +1.611 | [+0.890, +2.371] | 1 / 7 / 16 | -0.218 | -3.260 |
| value3 − none3 | -23.635 | [-28.249, -19.091] | 23 / 1 / 0 | +3.509 | +52.476 |
| value12 − none12 | -0.116 | [-0.345, +0.000] | 2 / 22 / 0 | +0.017 | +0.248 |
| value3 − rule3 | -21.872 | [-26.601, -17.162] | 23 / 1 / 0 | +3.422 | +51.182 |
| value12 − rule12 | +13.078 | [+10.056, +16.633] | 0 / 1 / 23 | -2.023 | -30.577 |
| none12 − none6 | -11.364 | [-16.147, -6.826] | 17 / 7 / 0 | +1.651 | +24.637 |
| value12 − value6 | -0.049 | [-4.161, +3.695] | 7 / 1 / 16 | -0.005 | -0.122 |

## What the terminal priority changes

Lexicographic objectives preserve minimum forecast unserved energy. The continuation arm next minimizes shortfall against a soft stock target and then minimizes throughput. No-continuation skips the target stage. Both then minimize current shedding, charging and discharge in sequence, fixing every component of the executed action by the flow and SOC balances. Two equally valuable future tails may still differ.

The terminal target adds a development-only estimate to the physical ending floor. By four-hour boundary-clock bin, the extra inventory estimates were 0.00, 69.09, 112.39, 34.27, 0.00, 0.00 MWh. They come from the 75th percentile of each window’s maximum cumulative future net energy draw, floored at zero, over six hours on eight original base days. No extra stock is requested beyond the end of the day. The estimator omits future ramp and reserve interactions and pools samples within clock bins. It approximates a future service risk. All arms start with the same hard physical feasible set. The achieved soft target selects a subset of the service-optimal plans before throughput is minimized.

## Reproduction and failure accounting

The original W03 replay matched every archived hourly action across 72 trajectories. The largest absolute component difference was 0. The Linux comparison for outage_reserve_864 differed by -1.898633 MWh of realized daily shedding. At zero-based hour 11, both first actions admitted a completion with the same optimal forecast service loss and throughput. These are 39.04395045 MWh and 62.13785914 MWh. Forcing the single Linux first action on the Mac reproduced the complete Linux action sequence with maximum difference 0. The deterministic service-first action tie-break agreed between primal-dual interior point and dual simplex on this one day. A full independent W04 Linux replay remains open.

The raw file holds 864 daily trajectories and 20,736 hourly actions, including the offline reference. Independent flow, energy, exclusivity, rate and reserve replay found maximum residual 7.11e-14. There were 21 fallback decisions. Four deliberately corrupted trajectories failed the checker. The second pass repeated all 864 trajectories, with 859 exactly equal action arrays. The largest action-component difference was 16.7. Its extra plan capture preserves forecast-horizon trajectories and terminal SOCs. This is a same-machine replay.

On the actual second pass the H6 continuation effect versus the rule was -5.063 MWh/day ([-8.259, -1.981]), and versus matched H6 without continuation it was -11.459 ([-15.959, -7.193]). The two live passes had different fallback signals on 12 trajectories. In a separate diagnostic, every nonidentical first-pass trajectory (5) was solved again with its originally observed clock signal forced at the deadline decision. Of these 0 still differed in actions. The diagnostic has access to prior runtime information and supplies no primary service or timing result.

A post hoc sensitivity retained a latent day only if both H6 arms had no fallback in any of its three regimes. Continuation minus rule was -4.565 MWh/day on 23 complete days, and continuation minus none was -10.660 on 22 complete days. This omits timeout-affected days and cannot replace the predeclared all-day estimand. Resampled intervals and included seeds are in results/deadline_sensitivity.json.

The fallback action was computed and validated before each candidate solve. The synchronous implementation can nevertheless return after the one-second gate. The maximum primary time at the rejection check was 3.840 s. Separate reconstruction of each used fallback (ten attempts per state) took at most 0.076 ms on this replay. The original instrumentation did not timestamp fallback readiness or demonstrate asynchronous execution at one second. Physical feasibility and selection on deadline are checked. On-time physical actuation remains unverified.

The independent forecast-tail audit checked 13,896 plans. It flagged 0 missing or infeasible plans. The maximum discrepancy between recorded lexicographic objectives and reconstructed forecast service/throughput was 1.28e-13 MWh. Soft target miss counts by arm are in results/plan_validation.json. A soft target can be unreachable after the minimum forecast service is fixed.

The first development attempt mixed a preinitialized default-thread HiGHS context with a forced single-thread context and returned Not Set. The thread settings were reconciled before freezing. The design, code, input and calibration hashes are in protocol/freeze.json. All cases and arms were retained. No held-out outcomes were used to revise the controller.

## Scope

This panel uses synthetic issued forecasts generated from a fixed stochastic process and a deterministic receding-horizon optimizer. Multiple regimes on one day share the underlying load. Reusing model assumptions and a small development set limits external validity. A longer model with additional forecasts changes the information available to the optimizer. It does not isolate solver improvement. See EXPLORATORY.md for the separate tail-information intervention. No operational telemetry, capacity credit, demand response payment, degradation valuation, or commercial SLA outcome enters these results.
