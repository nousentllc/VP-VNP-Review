"""Derive cohort counts, capped latency and descriptive paired comparisons from recorded trials."""
import csv
import gzip
import json
from collections import Counter,defaultdict
from statistics import median
import numpy as np
from common import OUT,DESIGN,save


def group(rows,keys):
    g=defaultdict(list)
    for r in rows:g[tuple(r[k] for k in keys)].append(r)
    return g


def paired_interval(values):
    arr=np.asarray(values)
    if not len(arr):return None
    rng=np.random.default_rng(9241)
    sample=rng.choice(arr,(5000,len(arr)),replace=True)
    return [float(v) for v in np.quantile(np.median(sample,axis=1),[.025,.975])]


def csvwrite(path,records):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)


def run():
    rows=[json.loads(v) for v in gzip.open(OUT/'A/holdout.jsonl.gz','rt')]
    acells=[]
    for (cohort,policy),rs in sorted(group(rows,['cohort','policy']).items()):
        by=group(rs,['case'])
        times=[median(2 if r['target_time'] is None else r['target_time'] for r in case) for case in by.values()]
        acells.append(dict(cohort=cohort,policy=policy,cases=len(by),attempts=len(rs),
                  target_hits=sum(r['target_time'] is not None for r in rs),
                  cases_all_repeats_hit=sum(all(r['target_time'] is not None for r in s) for s in by.values()),
                  median_case_capped_ms=1000*median(times),
                  median_first_feasible_ms=1000*median(r['first_feasible'] for r in rs),
                  solver_schedule_by_deadline=sum(r['first_solver_schedule'] is not None for r in rs),
                  best_is_fallback=sum(r['winner']=='fallback' for r in rs),
                  grouped_stage_target_hits=sum(str(r.get('target_stage','')).startswith('shared_') for r in rs)))
    csvwrite(OUT/'A/cohorts.csv',acells)
    pairs=[]
    for cohort in DESIGN['A']['cohorts']:
        by=group([r for r in rows if r['cohort']==cohort],['case','policy'])
        names=sorted({k[0] for k in by})
        def timing(name,method):
            return median(2 if r['target_time'] is None else r['target_time'] for r in by[name,method])
        for ref in ['full_milp','full_lp','lp_recovery']:
            delta=[1000*(timing(n,'adaptive')-timing(n,ref)) for n in names]
            pairs.append(dict(cohort=cohort,comparator=ref,n_cases=len(names),median_ms=median(delta),
                              descriptive_case_bootstrap95_ms=paired_interval(delta),case_differences_ms=delta))
    save(OUT/'A/paired.json',pairs)
    Abranches=[]
    for r in rows:
        if r['repeat']!=0:continue
        for step in r['steps']:
            Abranches.append(dict(case=r['case'],policy=r['policy'],stage=step['label'],status=step['status'],
                       valid=step.get('returned_check',{}).get('valid'),candidate_cost=step.get('returned_check',{}).get('cost'),
                       groups=step['groups'],columns=step['columns'],binaries=step['binary'],rows=step['rows']))
    csvwrite(OUT/'A/stages_first_repeat.csv',Abranches)
    ac=json.loads((OUT/'C/runs.json').read_text())
    crows=[]
    for (name,method),rs in sorted(group(ac,['case','policy']).items()):
        ok=[r for r in rs if r.get('check',{}).get('valid') and r['within_deadline']]
        crows.append(dict(case=name,method=method,validated=len(ok),attempts=len(rs),
                          objective=median(r['check']['cost'] for r in ok) if ok else None,
                          lower=rs[0].get('dispatch_lower'),median_ms=median(r['elapsed'] for r in ok)*1000 if ok else None,
                          jacobian_nnz=rs[0].get('jacobian_nnz'),n_variables=rs[0].get('n_variables')))
    csvwrite(OUT/'C/comparison.csv',crows)
    dr=[]
    for p in sorted((OUT/'D').glob('*.json')):
        r=json.loads(p.read_text())
        if 'id' not in r:continue
        dr.append(dict(instance=r['instance'],hours=r['hours'],method=r['policy'],pairs=len(r['pairs']),
                       terminal_status=r['status'],valid_on_time=r['validated_by_deadline'],
                       cost=r.get('check',{}).get('objective'),solver_lower=r.get('solver_dual'),
                       bound_scope=r.get('bound_scope','unavailable'),build_seconds=r['build_seconds'],
                       elapsed=r['elapsed'],starts=r.get('check',{}).get('starts')))
    csvwrite(OUT/'D/comparison.csv',dr)
    e=json.loads((OUT/'E/runs.json').read_text());er=[]
    for (regime,),rs in sorted(group(e,['regime']).items()):
        pp=group(rs,['case','method']);ids=sorted({k[0] for k in pp})
        vals=lambda method,key:np.array([pp[i,method][0][key] for i in ids])
        diff=vals('rolling_mpc','unserved_MWh')-vals('forecast_rule','unserved_MWh')
        for m in DESIGN['E']['methods']:
            er.append(dict(regime=regime,policy=m,n=len(ids),unserved_total=sum(vals(m,'unserved_MWh')),
                        useful_compute_total=sum(vals(m,'useful_compute_MWh')),loss_total=sum(vals(m,'conversion_loss_MWh')),
                        throughput_total=sum(vals(m,'throughput_MWh')),peak_grid_mw=max(vals(m,'peak_import_MW')),
                        unavailable_reserve_mwh_equivalent=sum(vals(m,'unavailable_contracted_headroom_MWh_equivalent')),
                        terminal_min=min(vals(m,'terminal_MWh')),fallback_hours=sum(len(pp[i,m][0]['invalid_or_late_fallback_hours']) for i in ids)))
        if any(vals('perfect_foresight','unserved_MWh')-np.minimum(vals('forecast_rule','unserved_MWh'),vals('rolling_mpc','unserved_MWh'))>1e-5):
            raise ValueError('Offline solver failed a feasible online bound')
        pairs.append(dict(regime=regime,delta_mpc_minus_rule=diff.tolist(),
                          median=median(diff),descriptive_case_bootstrap95=paired_interval(diff),
                          mpc_wins=int(sum(diff < -1e-5)),ties=int(sum(abs(diff)<=1e-5)),losses=int(sum(diff>1e-5))))
    csvwrite(OUT/'E/comparison.csv',er)
    save(OUT/'E/paired.json',[x for x in pairs if 'regime' in x])


if __name__=='__main__':run()
