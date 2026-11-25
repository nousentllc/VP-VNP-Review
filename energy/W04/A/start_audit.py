"""Post-run administration of start evidence, model validation and trace interpretation."""
import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
import statistics as st
import argparse


def run(out):
    with gzip.open(out/'trials.jsonl.gz','rt') as f:rows=[json.loads(s) for s in f]
    stats=defaultdict(Counter);stages=defaultdict(Counter);grouped_root=Counter()
    first=defaultdict(list);levels=defaultdict(list);over=defaultdict(list)
    max_error=0.
    for r in rows:
        arm=r['arm'];cohort=r['cohort'];key=arm+' / '+cohort
        first[key].append(r['events'][0]['at'])
        over[key].append(max(0,r['wall']-2))
        cutoff=0.
        for stage in r['stages']:
            status=stage['status']
            stages[(arm,cohort,stage['label'])][status]+=1
            if stage['label']=='shared_1' and cohort=='forced_opposition':grouped_root[status]+=1
            if stage['full_model']:
                stats[key]['unrestricted_calls']+=1
                n,t=r['n'],r['t']
                assert stage['groups']==n and stage['columns']==4*n*t+t
                logs=stage.get('solver_evidence',[])
                costs=[float(m[1]) for s in logs if (m:=re.search(r'MIP start solution is feasible, objective value is ([-+.0-9eE]+)',s,re.I))]
                source=stage.get('start_source')
                stats[key]['source_'+str(source)]+=1
                if costs:
                    candidates=[v for v in r['witnesses'] if v['stage']==source and v['valid'] and v['at']<=max(cutoff, r['events'][0]['at'])+1e-6]
                    if not candidates:raise ValueError((r['case'],arm,source,cutoff))
                    expected=min(v['cost'] for v in candidates)
                    error=abs(expected-costs[0]);max_error=max(max_error,error)
                    if error>2e-5:raise ValueError(('Transferred objective mismatch',r['case'],source,expected,costs[0]))
                    stats[key]['solver_confirmed_start_cost_matches_prior_feasible_witness']+=1
                    if source!='fallback':stats[key]['confirmed_nonfallback']+=1
                else:stats[key]['no_solver_objective_acknowledgement']+=1
                levels[key].append(stage.get('start_check_transfer_seconds',0))
            cutoff=max(cutoff,stage.get('end',0))
    payload=dict(start_evidence=stats,root_status_forced_stratum=grouped_root,
                 stage_results=[{'arm':a,'cohort':c,'stage':s,'statuses':dict(states)} for (a,c,s),states in stages.items()],
                 max_confirmed_cost_discrepancy=max_error,median_start_transfer_ms={k:1000*st.median(vals) for k,vals in levels.items()},
                 median_fallback_validation_ms={k:1000*st.median(vals) for k,vals in first.items()},
                 max_overrun_seconds={k:max(vals) for k,vals in over.items()})
    (out/'start_audit.json').write_text(json.dumps(payload,indent=2)+'\n')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);run(ap.parse_args().out)
