"""Supplementary audit of unexecuted forecast tails from the full second pass."""
import gzip
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent


def main(repeat=ROOT/'results/repeat.jsonl.gz', plans=ROOT/'results/projected_plans.jsonl.gz',
         output_path=ROOT/'results/plan_validation.json'):
    P=json.loads(gzip.decompress((ROOT/'inputs/holdout.json.gz').read_bytes()))
    params=P['parameters'];cases={c['id']:c for c in P['cases']}
    with gzip.open(repeat,'rt') as replay:
        shots={(r['case'],r['policy']):r for r in map(json.loads,replay)}
    seen=set()
    summary={};invalid=[];rows=0;absobj=0.
    with gzip.open(plans,'rt') as f:
        for line in f:
            rec=json.loads(line);case=cases[rec['case']];arm=rec['policy']
            key=(rec['case'],arm)
            if key in seen:raise ValueError(f'Duplicate projected plan record: {key}')
            seen.add(key)
            run=shots[key]
            counts=summary.setdefault(arm,dict(plans=0,steps=0,worst=0.,unmet_soft_target=0,requested_above_floor=0))
            planned=rec['predicted_plans']
            if arm.startswith('rule'):
                assert len(rec['rule_target_if_recharging'])==24 and not planned
                continue
            assert len(planned)==(1 if arm=='offline' else 24)
            for h,trajectory in enumerate(planned):
                if trajectory is None:
                    invalid.append([case['id'],arm,h,'no_plan'])
                    continue
                a=np.asarray(trajectory);H=len(a);g,ch,ds,u,s=a.T
                prev=run['actions'][h-1][0] if h else params['previous']
                e=run['actions'][h-1][4] if h else params['initial']
                issue=case['issues'][h]
                demand=np.array(case['load'] if arm=='offline' else issue['load'][:H],dtype=float)
                av=np.array(case['available'] if arm=='offline' else issue['available'][:H],dtype=bool)
                if arm=='value12_tail6' and H>6:demand[6:]=demand[5]
                reserve=np.array(case['reserve'][h:h+H]);floor=np.array(case['floor'][h:h+H])
                worst=max(0.,abs(s-(e+np.cumsum(ch*params['eta_c']-ds/params['eta_d']))).max(),
                          (floor-s).max(),(s-params['energy']).max(),np.minimum(ch,ds).max(),
                          (ch-params['power']*av).max(),(ds-np.maximum(0.,params['power']*av-reserve)).max(),
                          abs(g+ds-ch+u-demand).max(),(abs(np.diff(np.r_[prev,g]))-params['ramp']).max(),
                          (g-params['grid_cap']).max(),-a.min(),(u-demand+params['facility']).max())
                counts['worst']=float(max(counts['worst'],worst));counts['plans']+=1;counts['steps']+=H;rows+=1
                if worst>1e-6:invalid.append([case['id'],arm,h,worst])
                log=run['decisions'][h];target=log['end_target']
                if target is not None:
                    counts['requested_above_floor']+=int(target>floor[-1]+1e-6)
                    counts['unmet_soft_target']+=int(target>s[-1]+1e-6)
                if 'forecast_unserved' in log['objectives']:
                    absobj=max(absobj,abs(sum(u)-log['objectives']['forecast_unserved']),
                               abs(sum(ch+ds)-log['objectives']['throughput']))
    if seen!=set(shots):raise ValueError('Projected plan panel differs from the second-pass panel.')
    output=dict(scope='Second-pass projected tails and real actions are distinct. Soft target misses are permitted.',summary=summary,
                invalid_or_missing=invalid,checked_plans=rows,max_two_objective_residual=float(absobj))
    output_path.write_text(json.dumps(output,indent=2)+'\n')


if __name__=='__main__':main()
