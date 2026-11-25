"""Build track claim index from the shipped evidence and summaries."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    with (ROOT/'results/paired_effects.csv').open() as f:
        effects={(x['arm'],x['baseline'],x['regime']):x for x in csv.DictReader(f)}
    def quantitative(a,b,reg):
        row=effects[a,b,reg]
        return (f'{a} minus {b}, {reg}: {float(row["delta_unserved_mean"]):+.3f} MWh/day, '
                f'descriptive day-cluster 95% interval [{float(row["ci_low"]):+.3f}, {float(row["ci_high"]):+.3f}].')
    ver=json.loads((ROOT/'results/validation.json').read_text())
    clock=json.loads((ROOT/'results/deadline_attribution.json').read_text())
    repeat=ver['same_machine_repeat']
    entries=[
        ('E1','reproduced','All 72 native W03 trajectories matched their archived hourly actions.','Original frozen W03 inputs; the wall gate can vary.','protocol/development.json; results/W03_replay.json.gz','Any rerun action difference under the original deadline pattern.'),
        ('E2','mechanism reproduced on one historical case','At hour index 11 on outage_reserve_864 distinct first actions achieved identical optimal forecast service and throughput. Substituting the archived Linux action reproduced its entire trajectory.','Two-stage W03 LP; supplied Linux trajectory; same original issued forecasts.','results/linux_case_diagnostic.json; protocol/development.json; protocol/reviewer_lineage.json','Either conditioned first-action optimum differs or Linux substitution fails to recover later actions.'),
        ('E3','supported on synthetic panel',quantitative('value6','none6','all'),'Three regimes nested in each of 24 fresh days; same H6 forecasts, physical set and tie breaking. Internal replay.','results/paired_effects.csv; results/paired_days.csv; protocol/freeze.json','Mean gain fails 0.1 MWh/day gate, interval includes zero or any accepted action violates tolerance.'),
        ('E4','supported on synthetic panel',quantitative('value6','rule6','all'),'All 24 complete latent days; strong matched rule; includes deadlines. Conversion loss and throughput increase.','results/regime_totals.csv; results/paired_effects.csv; results/pareto.csv','Mean gain fails 0.1 MWh/day gate, interval includes zero or any accepted action violates tolerance.'),
        ('E5','no benefit established',quantitative('value6','rule6','outage_reserve'),'Scheduled reserve and outage can share a visible event window; physically unavailable reserve is counted.','results/paired_effects.csv; inputs/holdout.json.gz','A prespecified new independently generated outage panel with a material negative interval would support an outage benefit.'),
        ('E6','matched H12 strategy defeated',quantitative('value12','rule12','all'),'Same 12-hour issue and same hard constraints. Identical terminal estimator across H arms.','results/paired_effects.csv','Material, validated service reduction against the H12 forecast rule.'),
        ('E7','diagnostic on fixed controller',quantitative('value12','value12_tail6','all'),'Both H12; sixth load issue held flat in control. No extra outage information. Flat alternative is only one imputation.','results/paired_effects.csv; results/tail_accuracy.csv; EXPLORATORY.md','Different effects under alternative tail imputations, different days or controllers limit transfer.'),
        ('E8','validated in simulated trajectories',f'All {ver["hourly_actions"]} primary actions passed independent replay; maximum residual {ver["max_residual"]:.4g}. {ver["fallbacks"]} actions used fallback.','Synthetic grid cap, rate, reserve, efficiency, facility, SOC and terminal constraints; tolerance 1e-6.','results/validation.json; results/scenario_metrics.csv; results/deadline_sensitivity.json','Any recomputed violation above tolerance or accepted trajectory below the offline lower objective.'),
        ('E9','conditional same-machine attribution',f'Live passes matched {repeat["exact_action_trajectories"]}/{repeat["total"]} trajectories exactly. {clock["original_clock_trajectories_with_unequal_actions"]} of {clock["rerun_count"]} differing trajectories remained unequal after forcing original observed deadline signals.','Same host, solver, data, code. Forced clock is a diagnostic. On-time asynchronous fallback delivery untested.','results/validation.json; results/deadline_attribution.json; results/repeat_summary/paired_effects.csv','Any differences surviving fixed deadline signals or independent cross-platform discrepancy.'),
        ('E10','untested','Plant performance, independent W04 Linux replication, real-time fallback actuation and jobs/degradation economics remain open.','No operational trace, physical plant, contractual economic model or independent W04 operating-system run.','FINDINGS.md; protocol/design.md','Independent real-world data and timing instrumentation would be needed for these outcomes.'),
    ]
    with (ROOT/'claims.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['id','status','claim','assumptions','locator','falsifier']);w.writerows(entries)

if __name__=='__main__':
    main()
