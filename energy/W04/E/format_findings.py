"""Create the editable track memo from verified summaries; intended once both runs have finished."""
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def getcsv(name):
    with (ROOT/'results'/name).open() as f:return list(csv.DictReader(f))


def select(rows,**match):
    return next(x for x in rows if all(x[k]==v for k,v in match.items()))


def main():
    metrics=getcsv('regime_totals.csv')
    pairs=getcsv('paired_effects.csv')
    ver=json.loads((ROOT/'results/validation.json').read_text())
    if not (ROOT/'results/deadline_sensitivity.json').exists():
        import deadline_sensitivity
        deadline_sensitivity.main()
    sensitivity=json.loads((ROOT/'results/deadline_sensitivity.json').read_text())
    clean={row['comparator']:row for row in sensitivity['primary']['complete_days']}
    clock=json.loads((ROOT/'results/deadline_attribution.json').read_text())
    second_rows=getcsv('repeat_summary/paired_effects.csv')
    secondary=select(second_rows,arm='value6',baseline='rule6',regime='all')
    secondary2=select(second_rows,arm='value6',baseline='none6',regime='all')
    plan_audit=json.loads((ROOT/'results/plan_validation.json').read_text())
    dev=json.loads((ROOT/'protocol/development.json').read_text())
    diag=json.loads((ROOT/'results/linux_case_diagnostic.json').read_text())
    def contrast(a,b,g='all'):return select(pairs,arm=a,baseline=b,regime=g)
    def signed(r,Key='delta_unserved_mean'):return f'{float(r[Key]):+.3f}'
    def interval(r):return f'[{float(r["ci_low"]):+.3f}, {float(r["ci_high"]):+.3f}]'
    def summary(a,b):
        r=contrast(a,b);return f'{signed(r)} MWh/day, descriptive 95% interval {interval(r)}'
    target=contrast('value6','none6')
    target_pass=float(target['delta_unserved_mean'])<-.1 and float(target['ci_high'])<0 and ver['max_residual']<=1e-6
    dominance=select(getcsv('pareto.csv'),arm='value6',reference='rule6',regime='all')
    r=contrast('value6','rule6')
    passed=float(r['delta_unserved_mean'])<-.1 and float(r['ci_high'])<0 and ver['max_residual']<=1e-6
    repro=ver.get('same_machine_repeat',{})
    lines=['# W04-E · Continuation value and prediction horizon','',
           f'The six-hour continuation controller changed flexible unserved energy by **{summary("value6","none6")}** against the same deterministic six-hour controller without continuation. Against the strong matched-horizon rule its difference was **{summary("value6","rule6")}**. A negative difference favors the continuation controller. At fixed H6 the continuation-versus-none gate **{"passed" if target_pass else "did not pass"}**. The preregistered service-benefit gate against the rule **{"passed" if passed else "did not pass"}** on this synthetic panel.','',
           '## Panel, information and estimands','',
           'Twenty-four new latent 24-hour days each appear under ordinary, biased-forecast and outage/reserve conditions. Each issue supplies a shared twelve-hour maximum forecast. A shorter policy sees only its prefix. The current observation and next-hour explicit outage disclosure are common. In the generator, the reserve schedule starts two hours before the workload peak starts, and the outage starts one hour after that peak starts. The public reserve calendar and the load forecast can therefore indirectly signal the event window beyond one hour. All matched arms receive the same schedule. The physical site has a 100 MW import cap, 23 MW/h ramp, 35 MW / 180 MWh battery, and a protected 24 MW noncurtailable facility load. The original reserve and terminal floors apply to every policy. Charge/discharge efficiencies are 0.94/0.93, opening inventory is 95 MWh and the closing minimum is 95 MWh. When an outage prevents the scheduled reserve from being supplied, dispatch power falls to zero and the unavailable obligation is counted separately. The offline benchmark sees actual future load and availability.','',
           'The twelve arms include three matching forecast rules, six deterministic horizon/terminal factorial controllers, the legacy W03 six-hour optimizer, one six-hour-information/twelve-hour-model diagnostic, and one offline reference. Each online arm applied its own observed state to the same prevalidated fallback rule. An individual action had a one-second wall gate. All comparisons are matched by day and regime. The primary mean first averages the three regime differences within each day. Intervals resample 24 whole days 10,000 times. All secondary intervals are descriptive and unadjusted.','',
           '## Service and resource tradeoffs','',
           '| Regime | H6 policy | Unserved MWh, 24 days | Conversion loss MWh | Battery throughput MWh | P95 decision ms |',
           '|---|---|---:|---:|---:|---:|']
    for g in ['base','biased_forecast','outage_reserve']:
        for a in ['rule6','none6','value6','offline']:
            x=select(metrics,regime=g,policy=a)
            lines.append(f'| {g} | {a} | {float(x["unserved"]):,.2f} | {float(x["losses"]):,.2f} | {float(x["throughput"]):,.2f} | '+('offline' if a=='offline' else f'{float(x["p95_ready_ms"]):.2f}')+' |')
    stratum=[]
    for regime in ['base','biased_forecast','outage_reserve']:
        v=contrast('value6','rule6',regime)
        stratum.append(f'{regime} {signed(v)} {interval(v)}')
    lines+=['','H6 continuation minus the matched rule by regime, in MWh/day with day-bootstrap intervals: '+', '.join(stratum)+'. The outage/reserve interval includes zero. At H12 the matched rule served more load than the continuation controller on average.','',
            'The offline rows report a full-day physical comparison. Their solve time is recorded separately. Loss and throughput are physical quantities. No degradation price or useful-job conversion was supplied. The controller rankings depend on which outcome is valued. The complete regime table also reports served load, import peak, terminal SOC and unavailable reserve headroom.','',
            f'Across the 72 H6 comparisons against the rule, the continuation policy was weakly better in all three of unserved energy, conversion loss and throughput and strictly better in at least one on {dominance["first_dominates"]} cases. The rule dominated on {dominance["second_dominates"]}, {dominance["equivalent"]} tied in all three, and {dominance["tradeoff"]} had opposing changes. The tolerance for each quantity was 0.000001 MWh. These are descriptive scenario counts. The regimes within a day are dependent.','',
            '| Comparison, first minus second | Mean unserved MWh/day | Day interval | Days lower / tied / higher | Mean conversion loss Δ MWh/day | Mean throughput Δ MWh/day |',
            '|---|---:|---:|---:|---:|---:|']
    for a,b in [('value6','none6'),('value6','rule6'),('none6','legacy6'),('value3','none3'),('value12','none12'),
                ('value3','rule3'),('value12','rule12'),('none12','none6'),('value12','value6')]:
        r=contrast(a,b)
        lines.append(f'| {a} − {b} | {signed(r)} | {interval(r)} | {r["wins"]} / {r["ties"]} / {r["losses"]} | {signed(r,"mean_delta_conversion_loss")} | {signed(r,"mean_delta_throughput")} |')
    lines+=['','## What the terminal priority changes','',
            'Lexicographic objectives preserve minimum forecast unserved energy. The continuation arm next minimizes shortfall against a soft stock target and then minimizes throughput. No-continuation skips the target stage. Both then minimize current shedding, charging and discharge in sequence, fixing every component of the executed action by the flow and SOC balances. Two equally valuable future tails may still differ.','',
            'The terminal target adds a development-only estimate to the physical ending floor. By four-hour boundary-clock bin, the extra inventory estimates were '+', '.join(f'{q:.2f}' for q in dev['calibration']['extra'])+' MWh. They come from the 75th percentile of each window’s maximum cumulative future net energy draw, floored at zero, over six hours on eight original base days. No extra stock is requested beyond the end of the day. The estimator omits future ramp and reserve interactions and pools samples within clock bins. It approximates a future service risk. All arms start with the same hard physical feasible set. The achieved soft target selects a subset of the service-optimal plans before throughput is minimized.','',
            '## Reproduction and failure accounting','',
            f'The original W03 replay matched every archived hourly action across {dev["archived_trajectories"]} trajectories. The largest absolute component difference was {dev["max_W03_action_difference"]:.3g}. The Linux comparison for outage_reserve_864 differed by {dev["linux_unserved"]-dev["mac_unserved"]:+.6f} MWh of realized daily shedding. At zero-based hour {dev["first_divergent_hour"]}, both first actions admitted a completion with the same optimal forecast service loss and throughput. These are {dev["matched_first_action_subproblems"]["mac"]["stages"]["forecast_unserved"]:.8f} MWh and {dev["matched_first_action_subproblems"]["mac"]["stages"]["throughput"]:.8f} MWh. Forcing the single Linux first action on the Mac reproduced the complete Linux action sequence with maximum difference {diag["replay_with_one_linux_action_max_error_vs_linux"]:.3g}. The deterministic service-first action tie-break agreed between primal-dual interior point and dual simplex on this one day. A full independent W04 Linux replay remains open.','',
            f'The raw file holds {ver["trajectories"]} daily trajectories and {ver["hourly_actions"]:,} hourly actions, including the offline reference. Independent flow, energy, exclusivity, rate and reserve replay found maximum residual {ver["max_residual"]:.3g}. There were {ver["fallbacks"]} fallback decisions. Four deliberately corrupted trajectories failed the checker. The second pass repeated all {repro.get("total",0)} trajectories, with {repro.get("exact_action_trajectories",0)} exactly equal action arrays. The largest action-component difference was {repro.get("max_difference",0):.3g}. Its extra plan capture preserves forecast-horizon trajectories and terminal SOCs. This is a same-machine replay.','',
            f'On the actual second pass the H6 continuation effect versus the rule was {signed(secondary)} MWh/day ({interval(secondary)}), and versus matched H6 without continuation it was {signed(secondary2)} ({interval(secondary2)}). The two live passes had different fallback signals on {clock["live_trajectories_with_different_fallbacks"]} trajectories. In a separate diagnostic, every nonidentical first-pass trajectory ({clock["rerun_count"]}) was solved again with its originally observed clock signal forced at the deadline decision. Of these {clock["original_clock_trajectories_with_unequal_actions"]} still differed in actions. The diagnostic has access to prior runtime information and supplies no primary service or timing result.','',
            f'A post hoc sensitivity retained a latent day only if both H6 arms had no fallback in any of its three regimes. Continuation minus rule was {clean["rule6"]["mean_unserved_delta"]:+.3f} MWh/day on {clean["rule6"]["complete_days"]} complete days, and continuation minus none was {clean["none6"]["mean_unserved_delta"]:+.3f} on {clean["none6"]["complete_days"]} complete days. This omits timeout-affected days and cannot replace the predeclared all-day estimand. Resampled intervals and included seeds are in results/deadline_sensitivity.json.','',
            f'The fallback action was computed and validated before each candidate solve. The synchronous implementation can nevertheless return after the one-second gate. The maximum primary time at the rejection check was {sensitivity["primary"]["longest_observed_s"]:.3f} s. Separate reconstruction of each used fallback (ten attempts per state) took at most {1000*sensitivity["primary"]["longest_reconstructed_fallback_s"]:.3f} ms on this replay. The original instrumentation did not timestamp fallback readiness or demonstrate asynchronous execution at one second. Physical feasibility and selection on deadline are checked. On-time physical actuation remains unverified.','',
            f'The independent forecast-tail audit checked {plan_audit["checked_plans"]:,} plans. It flagged {len(plan_audit["invalid_or_missing"])} missing or infeasible plans. The maximum discrepancy between recorded lexicographic objectives and reconstructed forecast service/throughput was {plan_audit["max_two_objective_residual"]:.3g} MWh. Soft target miss counts by arm are in results/plan_validation.json. A soft target can be unreachable after the minimum forecast service is fixed.','',
            'The first development attempt mixed a preinitialized default-thread HiGHS context with a forced single-thread context and returned Not Set. The thread settings were reconciled before freezing. The design, code, input and calibration hashes are in protocol/freeze.json. All cases and arms were retained. No held-out outcomes were used to revise the controller.','',
            '## Scope','',
            'This panel uses synthetic issued forecasts generated from a fixed stochastic process and a deterministic receding-horizon optimizer. Multiple regimes on one day share the underlying load. Reusing model assumptions and a small development set limits external validity. A longer model with additional forecasts changes the information available to the optimizer. It does not isolate solver improvement. See EXPLORATORY.md for the separate tail-information intervention. No operational telemetry, capacity credit, demand response payment, degradation valuation, or commercial SLA outcome enters these results.']
    (ROOT/'FINDINGS.md').write_text('\n'.join(lines)+'\n')
    er=contrast('value12','value12_tail6');eh=contrast('value12_tail6','value6')
    tails=getcsv('tail_accuracy.csv')
    realtail=select(tails,regime='all',prediction='issued')
    flattail=select(tails,regime='all',prediction='flat')
    expl=f'''# Additional diagnostic · separating a longer model from a longer load forecast

**Rationale.** Comparing H6 and H12 directly changes both the information supplied and the decision horizon. The preregistered tail intervention keeps the twelve-hour optimization, terminal estimator, time-indexed floors and availability model fixed. It replaces load forecasts beyond the sixth entry with the sixth value held constant. Simulated actual loads and current observations are untouched. This is a controlled input intervention. A constant forecast is one explicit comparator, and the effect depends on that imputation.

**Fresh results.** With identical twelve-hour continuation control, supplying the actual issued load-forecast tail changed unserved energy by {signed(er)} MWh/day relative to constant-tail imputation (24-day interval {interval(er)}). The imputed H12 policy differed from the ordinary H6 continuation policy by {signed(eh)} MWh/day ({interval(eh)}). That second contrast includes model length, end-of-window target date, and the assumption specifying the tail. All effects are equal-weighted by day and regime. Individual differences are in results/paired_days.csv.

**Post hoc forecast scoring.** The inferior service under the issued tail raised a distinct question about forecast accuracy. Across {int(realtail["entries"]):,} issue/target pairs with lead 6–11, the issued tail had {float(realtail["mae_MW"]):.3f} MW absolute error on average versus {float(flattail["mae_MW"]):.3f} MW for a flat tail. RMSE was {float(realtail["rmse_MW"]):.3f} versus {float(flattail["rmse_MW"]):.3f} MW. These are descriptive scores on overlapping targets and shared days. The issued point forecast was more accurate by both metrics, yet using that forecast in this particular deterministic H12 controller resulted in greater realized shedding. No forecast model or decision policy was retuned. The comparison does not establish a general negative value of information for an optimal stochastic policy. See results/tail_accuracy.csv.

**Separate W03 diagnosis.** The Mac and reviewer Linux trajectories at outage_reserve_864 diverge at zero-based index 11 (hour 12). At that decision, two different admissible actions have the same optimal forecast shedding and cycling cost. The observed difference of 1.898633 MWh in realized service comes entirely from that one choice and its effect on future inventory. Injecting the Linux action on the Mac reproduced all remaining Linux outputs. The handling of equal optima therefore explains the archived discrepancy on these files without attributing it to forecast or physics differences. Both dual simplex and interior point reproduce the new deterministic tie-break on this single day. This does not constitute an independent cross-platform trial of the new campaign.
'''
    (ROOT/'EXPLORATORY.md').write_text(expl)


if __name__=='__main__':main()
