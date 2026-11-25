"""Analysis and independent battery replay. Execute after the frozen run."""
import argparse
import csv
import gzip
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from campaign import HERE, SEEDS, ARMS, COHORTS, arrays, model, save
from battery_audit import exact_box, direct


def write_csv(p, rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)


def run(out):
    cases={a['id']:arrays(a) for a in json.loads((HERE/'protocol/instances.json').read_text())}
    with gzip.open(out/'trials.jsonl.gz','rt') as f:raw=[json.loads(s) for s in f]
    assert len(raw)==72*3*5 and len({(x['case'],x['repeat'],x['arm']) for x in raw})==len(raw)
    exact=[];low={}
    for x in raw:
        if 'lp_dual' not in x:continue
        a=cases[x['case']];m,_,_=model(a,[[i] for i in range(a['n'])],kind='lp')
        l=exact_box(m,x['lp_dual']);low[x['case']]=float(l)
        exact.append(dict(case=x['case'],exact_rational_lower=str(l)))
    assert len(low)==72
    trials=[];start_log=[];stage_log=[];checked=0;reject=0;worst=0
    for x in raw:
        a=cases[x['case']];wits=x['witnesses'];ev=x['events'];L=low[x['case']]
        for w in wits:
            cost,err=direct(a,[w['c'],w['d']]);assert abs(cost-w['cost'])<2e-5
            assert (err<=2e-6)==w['valid'];checked+=1
            if w['valid']:worst=max(worst,err)
            else:reject+=1
        changes=[e for e in ev if 'U'in e]
        assert all(e['at']<=2 and wits[e['witness']]['valid'] and e['U']>=L-2e-5 for e in changes)
        first=next((e['at'] for e in changes if e['stage']!='fallback'),None)
        U=x['fallback_cost']; U0=U;last=0.;area=0.
        for e in changes:
            area+=(e['at']-last)*(U-L)
            last=e['at'];U=e['U']
        area+=(2-last)*(U-L)
        norm=area/(2*(U0-L)) if U0-L>1e-8 else None
        ub=lb=None; target=None
        for e in ev:
            ub=e.get('U',ub);lb=e.get('L',lb)
            if ub is not None and lb is not None and ub-lb<=.00002+.001*max(1,abs(ub)) and target is None:target=e['at']
        assert target==x['target']
        for k,v in x['snapshots'].items():
            events=[e for e in ev if 'U'in e and e['at']<=float(k)]
            assert v['U']==(events[-1]['U'] if events else None)
        item=dict(case=x['case'],cohort=x['cohort'],seed=a['seed'],arm=x['arm'],repeat=x['repeat'],
                  first_improvement=first,hit=bool(x['target'] is not None),capped_time=x['target'] or 2.,
                  area_normalized=norm,fallback=U0,wall=x['wall'],rss_highwater_native=x['resource_end'])
        for k,v in x['snapshots'].items():item['U_'+k]=v['U'];item['L_'+k]=v['L']
        trials.append(item)
        for stage in x['stages']:
            entry=dict(case=x['case'],arm=x['arm'],repeat=x['repeat'],stage=stage['label'],status=stage['status'],
            binary=stage['original_binary_count'],columns=stage['columns'],rows=stage['rows'],build=stage['build_seconds'],
            validate=stage['validation_seconds'],solve=stage.get('solve_with_callbacks_seconds'),
            transfer=stage.get('start_check_transfer_seconds'),source=stage.get('start_source'),
            set_status=stage.get('start_set_status'),confirmed=stage.get('start_confirmed_feasible'))
            stage_log.append(entry)
            if stage['full_model']:
                assert stage['original_binary_count']==a['n']*a['t']
                start_log.append(entry)
    write_csv(out/'trials.csv',trials);write_csv(out/'stages.csv',stage_log)
    group=defaultdict(list)
    for q in trials:group[q['case'],q['arm']].append(q)
    by_case=[]
    for (cid,arm),runs in group.items():
        a=cases[cid];row=dict(case=cid,arm=arm,cohort=a['cohort'],seed=a['seed'],n=a['n'],T=a['t'],
                              allhit=all(q['hit'] for q in runs),fallback=runs[0]['fallback'])
        for key in ['capped_time','area_normalized','first_improvement','wall','U_0.05','U_0.1','U_0.25','U_0.5','U_1.0','U_2.0']:
            values=[q[key] for q in runs if q[key] is not None]
            row[key]=statistics.median(values) if len(values)==3 else None
        by_case.append(row)
    write_csv(out/'case_medians.csv',by_case)
    lookup={(r['case'],r['arm']):r for r in by_case}
    contrasts=[];pairs=[];rng=np.random.default_rng(104033)
    for cohort in COHORTS:
        for base in ['full_milp','lp_repair_start','group_no_transfer']:
            for key in ['U_0.25','U_2.0','capped_time','area_normalized']:
                deltas=[];wins=ties=losses=0
                block=defaultdict(list)
                for cid,a in cases.items():
                    if a['cohort']!=cohort:continue
                    g,b=lookup[cid,'group_start'],lookup[cid,base]
                    if g[key] is None or b[key] is None:continue
                    d=g[key]-b[key];deltas.append(d);block[a['seed']].append(d)
                    tol=.001*max(1,abs(g['fallback'])) if key.startswith('U_') else 1e-7
                    wins+=d < -tol;losses+=d > tol;ties+=abs(d)<=tol
                    pairs.append(dict(case=cid,cohort=cohort,compared_to=base,measure=key,
                                      grouped=g[key],baseline=b[key],difference=d,threshold=tol))
                ci=[None,None]
                if block:
                    keys=sorted(block)
                    boots=[np.median([v for j in js for v in block[keys[j]]]) for js in rng.integers(0,len(keys),(5000,len(keys)))]
                    ci=np.quantile(boots,[.025,.975]).tolist()
                contrasts.append(dict(cohort=cohort,compared_to=base,measure=key,n=len(deltas),
                                 median=float(np.median(deltas)) if deltas else None,
                                 mean=float(np.mean(deltas)) if deltas else None,ci_low=ci[0],ci_high=ci[1],
                                 wins=wins,ties=ties,losses=losses))
    write_csv(out/'paired_case_differences.csv',pairs);write_csv(out/'contrasts.csv',contrasts)
    counts=[dict(cohort=c,arm=p,cases=18,all_repeats_hit=sum(r['allhit'] for r in by_case if r['cohort']==c and r['arm']==p),
                 trial_hits=sum(r['hit'] for r in trials if r['cohort']==c and r['arm']==p))
            for c in COHORTS for p in ARMS]
    write_csv(out/'target_counts.csv',counts)
    save(out/'audit.json',dict(case_count=len(cases),trial_count=len(raw),witnesses_checked=checked,
         inadmissible_witnesses=reject,worst_valid_residual=worst,exact_bounds=len(exact),
         start_processing={p:dict(unrestricted_calls=sum(s['arm']==p for s in start_log),
           confirmed_feasible=sum(s['arm']==p and s['confirmed']==True for s in start_log),
           nonfallback_confirmed=sum(s['arm']==p and s['confirmed']==True and s['source']!='fallback' for s in start_log))
           for p in ARMS},overruns=sum(q['wall']>2 for q in trials),max_wall=max(q['wall'] for q in trials)))
    save(out/'exact_bounds.json',exact)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);run(p.parse_args().out)
