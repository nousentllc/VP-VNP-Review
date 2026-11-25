"""Secondary sensitivity: complete latent days and independent fallback construction replay."""
import gzip
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import campaign

ROOT = Path(__file__).resolve().parent
REGIMES = ['base','outage_reserve','biased_forecast']


def audit(path):
    with gzip.open(path,'rt') as f:
        runs = [json.loads(line) for line in f]
    cases = {c['id']: c for c in campaign.read(ROOT/'inputs/holdout.json.gz')['cases']}
    data = {(r['seed'],r['regime'],r['policy']):r for r in runs}
    seed_set = sorted({r['seed'] for r in runs})
    timing = []
    for r in runs:
        case=cases[r['case']]
        for t,log in enumerate(r['decisions']):
            if log['fallback'] is None:
                continue
            prev,e=(r['actions'][t-1][0], r['actions'][t-1][4]) if t else (campaign.P['previous'],campaign.P['initial'])
            durations=[];error=0.
            for _ in range(10):
                start=perf_counter()
                issue=case['issues'][t]
                idx=np.array(issue['valid'][:log['horizon']])
                load=np.array(issue['load'][:len(idx)])
                available=np.array(issue['available'][:len(idx)])
                floors=np.asarray(case['floor'])[idx]
                reserves=np.asarray(case['reserve'])[idx]
                action=campaign.old.rule(load[:1],available[:1],floors[:1],reserves[:1],e,prev)
                residual=campaign.old.check(action,e,prev,case['load'][t],case['available'][t],floors[0],reserves[0])
                durations.append(perf_counter()-start)
                error=max(error,float(abs(action-r['actions'][t]).max()))
            timing.append(dict(case=r['case'],policy=r['policy'],issue=t,reason=log['fallback'],
                               original_candidate_ready_s=log['ready_seconds'],recheck_residual=residual,
                               max_action_error=error,ten_reconstruction_seconds=durations))
    clean=[]
    rng=np.random.default_rng(665411)
    for comparator in ('none6','rule6'):
        included=[];delta=[]
        for s in seed_set:
            pairs=[(data[s,g,'value6'],data[s,g,comparator]) for g in REGIMES]
            if any(x['fallback'] is not None for pair in pairs for r in pair for x in r['decisions']):
                continue
            included.append(s)
            delta.append(np.mean([a['unserved']-b['unserved'] for a,b in pairs]))
        arr=np.array(delta)
        if len(arr):
            ii=rng.integers(0,len(arr),size=(10000,len(arr)))
            left,right=np.quantile(arr[ii].mean(axis=1),[.025,.975])
            clean.append(dict(comparator=comparator,complete_days=len(arr),excluded_days=len(seed_set)-len(arr),
                              mean_unserved_delta=float(arr.mean()),ci_low=float(left),ci_high=float(right),included_seeds=included))
    return dict(complete_days=clean,late_checks=timing,
                longest_observed_s=max((r['original_candidate_ready_s'] for r in timing),default=0),
                longest_reconstructed_fallback_s=max((max(r['ten_reconstruction_seconds']) for r in timing),default=0))


def main(primary=ROOT/'results/holdout.jsonl.gz',repeat=ROOT/'results/repeat.jsonl.gz',
         output_path=ROOT/'results/deadline_sensitivity.json'):
    result=dict(scope='Complete case is post hoc. A day is retained only if neither H6 arm fell back in any of its three regimes. Prior clock or actuation times cannot be inferred from a new construction replay.',
                primary=audit(primary),second=audit(repeat))
    output_path.write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':
    main()
