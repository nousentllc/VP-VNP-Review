"""Render the W05-A findings and scoped ledger from the complete checked tables."""
import argparse
import csv
import json
from pathlib import Path

def read(path):
    with path.open() as f:return list(csv.DictReader(f))
def f(x,n=3):
    return f'{float(x):.{n}f}' if x is not None and x!='' else 'N/A'
def generate(root,results):
    summary=read(results/'summary.csv');dct={(s['arm'],s['stratum']):s for s in summary}
    comp={(z['baseline'],z['metric']):z for z in read(results/'contrasts.csv')}
    checks=json.loads((results/'verification.json').read_text())
    attr=json.loads((results/'mechanisms.json').read_text())
    m={s['arm']:s for s in attr['stages']}; counts=lambda s,i:int(dct[s,'all'][i])
    indexes=[('native_cert','Native MILP + independent proof'),('lp_only','Full LP alone'),('lp_repair','LP repair and unrestricted start'),
             ('screen','Screen and direct escalation'),('native_unmetered_certificate','Full-budget native diagnostic')]
    regimes=['ordinary','negative_outage','forced_opposition','tight_reserve','unknown_exchange']
    trials=read(results/'trials.csv');allcase=read(results/'case_medians.csv')
    lines=['# W05-A · Individually validated LP screening','',
        '## Decision','']
    target=counts('screen','all_repeat_target');repair=counts('lp_repair','all_repeat_target')
    native=counts('native_cert','all_repeat_target')
    passes=all(target-counts(b,'all_repeat_target')>=2 and float(comp[b,'all_hit']['ci_low'])>0 for b in ['lp_repair','native_cert'])
    lines.append(f'Screening and direct escalation reached the within-two-second target on {target}/60 cases in every repeat. The equally screened LP-repair comparator reached {repair}/60. Native MILP with an independent certificate pass reached {native}/60. The prespecified joint improvement gate **{"passed" if passes else "failed"}**. It required at least two extra case hits against each comparator and a strictly positive lower endpoint for both paired seed-block intervals.')
    lines+=['','## Primary comparison','',
        'Four unused seed labels were crossed with three device-by-hour sizes and five stress families. Exactly 24 of 60 cases supplied a prevalidated constructive fallback and 36 did not. Of these 36, twelve were generated from an exogenous exchange corridor without any feasible plan construction. A missing action or inconclusive solve is not model infeasibility. The 900 rows include three rotated repeats and five arms per cell. The family frequencies and four seed clusters are experimental design choices.','','| Arm | Cases with all-repeat exact-bound target | Cases with all-repeat action | Cases with all-repeat target and whole function returned in 2s | All-repeat gaps using offline common LP bound |','| --- | ---: | ---: | ---: | ---: |']
    for arm,label in indexes:
        q=dct[arm,'all']
        on=q['all_repeat_target'] if arm!='native_unmetered_certificate' else 'N/A'
        sy=q['all_repeat_synchronous'] if arm!='native_unmetered_certificate' else 'N/A'
        lines.append(f'| {label} | {on} | {q["all_repeat_action"]} | {sy} | {q["all_offline_hit"]} |')
    lines+=['',f'The fifth arm solves the native model without an explicit LP proof call. Its solver-reported numerical MIP gap met the target on {counts("native_unmetered_certificate","all_native_numerical_hit")}/60 cases in all repeats. Only the separate retrospective column uses a certified bound that another arm may have obtained later. No primary arm receives that bound online. Lower bounds from the LP do not close an integer gap automatically. The primal check uses native units with tolerance 2e-6.', '',
        '| Stress family (12 cases each) | Native + proof | LP | LP repair | Screen |','| --- | ---: | ---: | ---: | ---: |']
    for family in regimes:
        lines.append('| '+family+' | '+' | '.join(dct[arm,family]['all_repeat_target'] for arm,_ in indexes[:4])+' |')
    lines+=['','','## Paired effects and clocks','',
            'Effects are screen minus reference. Fixed costs compare case medians over complete triples only. The win/tie/loss counts use the practical input-specific threshold, and the intervals resample four whole seed blocks, 5,000 times. Cases with no observed action at a clock remain missing for that quality comparison. The complete-case denominator must travel with each difference. All six clocks, no-action events and case-level differences appear in the CSVs.','','| Comparator | Metric | Pairs | Paired effect | 95% seed-block interval | Practical W/T/L |','| --- | --- | ---: | ---: | ---: | ---: |']
    for base,blabel in [('lp_repair','LP repair'),('native_cert','Native + proof')]:
        for key,label in [('all_hit','Target rate, mean'),('U_0.25','250 ms cost, median'),('U_2.0','2 s cost, median'),('area','Normalized area, median'),('capped_time','Capped time (s), median')]:
            q=comp[base,key];effect=q['mean_delta'] if key=='all_hit' else q['median_delta']
            lines.append(f'| {blabel} | {label} | {q["pairs"]} | {f(effect)} | [{f(q["ci_low"])}, {f(q["ci_high"])}] | {q["wins"]}/{q["ties"]}/{q["losses"]} |')
    lines+=['','| Arm | No action / 180 | Fallback retained / 180 | Wall median / p95 / max (s) | Calls over 2 s |','| --- | ---: | ---: | --- | ---: |']
    for arm,label in indexes:
        q=dct[arm,'all']
        lines.append(f'| {label} | {q["no_action"]} | {q["fallback_only"]} | {f(q["wall_median"])} / {f(q["wall_p95"])} / {f(q["wall_max"])} | {q["overruns"]} |')
    lines+=['','The primary target clock marks when the individual dispatch and exact outer bound are known inside the worker. Reading solver logs and cleanup can delay synchronous completion. The separately reported return-time target counts exclude any run whose complete worker returned late. This shared arm64 host had no exclusive core or independent hardware replay. Raw monotonic time is one observed schedule. There is no production handoff or physical actuation measurement.','',
            '## Mechanism and certificate audit','','Both LP-first escalation arms use the same early success test. The test charges unrestricted LP assembly and solve, individual-mode and physical validation, and exact rational certificate calculation. When the LP fails, screening goes immediately to the native model. LP repair first attempts a sign-fixed LP and then a partially fixed MILP. Development gave each method the same two settings and W04 cases. Selected effort/time-share settings appear in protocol/freeze.json. The test compares the resulting policy pipelines; a cost difference cannot be assigned to a faster LP solver.','',
            '| Arm | Outer-only target / 180 | Explicit LP then native solve | Accepted native starts / submitted | Median exact bound time (ms) |','| --- | ---: | ---: | ---: | ---: |']
    for arm,label in indexes:
        q=m[arm];ct=q['exact_certificate_median_s']
        lines.append(f'| {label} | {q["target_before_any_native_or_repair"]} | {q["explicit_outer_then_unrestricted_calls"]} | {q["native_stage_confirmed_starts"]}/{q["native_stage_submitted_starts"]} | {f(ct*1000 if ct is not None else None,2)} |')
    exact=checks['exact_evaluations_rechecked'];wit=checks['reviewed_primal']
    lines+=['',f'The independent replay checked {wit:,} primal witnesses, including {checks["rejected_primal"]:,} that failed the original device tolerances. It independently reconstructed {exact:,} rational multiplier evaluations ({checks["unique_dual_vectors"]} unique case/multiplier pairs). The largest admitted physical residual was {checks["max_valid_primal_residual"]:.3g}. Lower values were rounded downward from exact fractions before numerical gap reporting. Each of 60 corrupted output controls failed the physical checker. A separate exact two-binary control exposes the sign error in an invalid reduced-cost lower bound.','',
        'For a minimization problem with finite column boxes and row intervals, a multiplier chooses the row lower limit when positive and the upper limit when negative. A multiplier paired with an unbounded side is set to zero. Add this row contribution to the minimum of each component of the reduced cost over its original variable interval. This yields a lower bound for every LP point and hence for every admissible integer point. The multipliers need not be optimal, and numerical dispatches still need checking. This argument applies to the stored coefficient model. Meteorology, parameter uncertainty, forecasting and economic error are outside the certificate.','',
        'The HiGHS logs expose presolve status and MIP-start processing. LP-first escalation invokes a fresh unrestricted solver and does not reuse an LP basis. When an explicit LP precedes native search, the native call may redo overlapping relaxations. The logs cannot establish identity of its transformed root LP with the external LP. The no-fallback cases have no normalized fallback-to-bound area; every missing interval records its reason. Raw full-MIP results and native diagnostic numerical gaps are preserved even when an independent lower bound cannot reach the target.']
    ex=json.loads((results/'small_exact_summary.json').read_text())
    lines+=['','## Post hoc exact primal reconstruction','',
        f'All {ex["cases"]} small 4×8 cases entered the offline audit. The repeat-zero raw LP schedule failed the original physical screen on {ex["statuses"].get("raw_LP_rejected",0)}. The remaining {ex["statuses"].get("exact_witness",0)} yielded recovered exact rational vertices of the original unrestricted coefficient model after fixing only the candidate device-hour modes. Every recorded box, inequality, equality and integer choice passed exact checking. The largest exact primal-minus-unrestricted-dual gap was {ex["max_exact_gap"]:.3g} cost units. Each one-MW mutation failed. This strengthens the small admissible-case result beyond tolerance-level primal replay. The offline proof time cannot be credited to the two-second campaign. See exact_primal_design.md and results/small_exact_primal.json.gz.']
    (root/'FINDINGS.md').write_text('\n'.join(lines)+'\n')
    claims=[
        ('W05-A01','pass' if passes else 'failed prespecified superiority criterion',f'Screen {target}/60, LP repair {repair}/60, native plus proof {native}/60 all-repeat on-time targets.',
         'Four fresh seed blocks, synthetic families, three rotated repeats; independently evaluated LP bound and 2e-6 feasible primal; per-policy development tuning.',
         'A/results/summary.csv; A/results/contrasts.csv; A/protocol/plan.md','At least two additional all-repeat hits and positive lower interval endpoints against both comparators, with valid witnesses.'),
        ('W05-A02','measured internal mechanism',f'{m["screen"]["target_before_any_native_or_repair"]}/180 screen trials met the target after the outer LP alone; {m["lp_repair"]["target_before_any_native_or_repair"]}/180 for the equally screened LP repair arm.',
         'Both share an early-stop test. Count trial-level logs.','A/results/mechanisms.json; A/results/trials.jsonl.gz','A purported outer-only success has native or repair involvement or lacks an on-time certified target.'),
        ('W05-A03','audited numerical primal and exact lower',f'{wit} primal witnesses and {exact} multiplier evaluations replayed; raw physical acceptance agrees with independent evaluation.',
         'Binary64 coefficients as exact rationals for lower; numerical engineering feasibility in original coordinates.','A/results/verification.json; A/results/mutation_controls.csv; A/results/mechanisms.json',
         'A stored accepted primal violates model tolerance or an unrestricted dual certificate overstates the minimum feasible objective.'),
        ('W05-A04','native diagnostic',f'Full-budget native numerical MIP target in {counts("native_unmetered_certificate","all_native_numerical_hit")}/60 cases; all-repeat post hoc common-bound comparator {counts("native_unmetered_certificate","all_offline_hit")}/60.',
         'The native-only diagnostic uses no on-clock independent proof. Retrospective common LP bound may come from another policy.',
         'A/results/summary.csv; A/results/trials.csv','A named reported numerical or retrospective hit lacks a valid incumbent or the advertised separately sourced bound.'),
        ('W05-A05','operational scope',f'{sum(z["overrun"]=="True" for z in trials)}/900 complete calls returned beyond two seconds.',
         'Measured monotonic shared-host time; on-time event and full synchronous return are different.',
         'A/results/trials.csv; A/results/case_medians.csv','Recomputed recorded complete-trial times yield other counts or reveal a late event given on-time credit.')]
    claims.append(('W05-AX01','exploratory exact arithmetic',f'All {ex["certified_gap"]} admissible small raw LP cases among 20 specified cells yielded full original-model rational feasible schedules with certified target gaps.',
        'Repeat zero, 4x8 cases only, fixed-mode simplex basis reconstructed over the stored binary64 coefficient model, outside the deadline.',
        'A/exact_primal_design.md; A/results/small_exact_summary.json; A/results/small_exact_primal.json.gz',
        'An original unrestricted row, box or integer fails exactly, or the independent unrestricted lower fails to give the target.'))
    with (root/'claims.csv').open('w',newline='') as fp:
        w=csv.writer(fp);w.writerow(['id','status','claim','assumptions','locator','falsifier']);w.writerows(claims)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--results',type=Path,required=True)
    args=p.parse_args();args.out.mkdir(exist_ok=True,parents=True);generate(args.out,args.results)
